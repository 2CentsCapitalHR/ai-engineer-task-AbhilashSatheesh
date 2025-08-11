import os
import json
import shutil
from typing import List, Dict, Any

import gradio as gr

from dotenv import load_dotenv

# Ensure src package on sys.path
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)
SRC_DIR = os.path.join(CURRENT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from src.config import AppConfig
from src.utils.file_utils import (
    ensure_directories,
    save_json_pretty,
    zip_files,
)
from src.utils.time_utils import now_timestamp_ist
from src.docx_tools.parser import read_docx_text
from src.docx_tools.annotator import annotate_docx_with_issues
from src.rules.checks import (
    REQUIRED_INCORP_DOCS,
    classify_document_type,
    detect_red_flags_rule_based,
    detect_process_by_content,
)
from src.rag.indexer import RAGIndexer
from src.rag.retriever import RAGRetriever
from src.llm.client import LLMClient


def build_services() -> Dict[str, Any]:
    config = AppConfig.from_env()
    ensure_directories([
        config.data_reference_dir,
        config.outputs_dir,
        config.vectorstore_dir,
    ])
    indexer = RAGIndexer(config=config)
    retriever = RAGRetriever(config=config)
    llm = LLMClient(config=config)
    return {
        "config": config,
        "indexer": indexer,
        "retriever": retriever,
        "llm": llm,
    }


def maybe_build_index(services: Dict[str, Any], force_rebuild: bool = False) -> str:
    indexer: RAGIndexer = services["indexer"]
    status = indexer.build_or_rebuild(force_rebuild=force_rebuild)
    return status


def analyze_documents(files: List[gr.File], rebuild_index: bool = False):
    services = build_services()
    config: AppConfig = services["config"]
    retriever: RAGRetriever = services["retriever"]
    llm: LLMClient = services["llm"]

    status_msg = maybe_build_index(services, force_rebuild=rebuild_index)

    uploaded_paths = [f.name if hasattr(f, 'name') else f for f in (files or [])]
    document_analysis: List[Dict[str, Any]] = []
    reviewed_paths: List[str] = []

    # Collect which required docs were present
    present_required_docs: set = set()

    for idx, path in enumerate(uploaded_paths):
        if not path or not os.path.exists(path):
            continue

        text = read_docx_text(path)
        doc_type = classify_document_type(text, filename=os.path.basename(path))
        if doc_type in REQUIRED_INCORP_DOCS:
            present_required_docs.add(doc_type)

        # Retrieve context for LLM/RAG
        contexts = retriever.retrieve(query=f"ADGM rules related to {doc_type}", top_k=5)

        # Rule-based findings
        issues_rule_based = detect_red_flags_rule_based(text, doc_type)

        # LLM-assisted findings (optional)
        issues_llm: List[Dict[str, Any]] = []
        if llm.is_enabled:
            issues_llm = llm.analyze_document(text=text, doc_type=doc_type, contexts=contexts)

        # Merge and add source citations (from retriever contexts)
        merged_issues: List[Dict[str, Any]] = []
        for issue in issues_rule_based + issues_llm:
            issue = dict(issue)
            # attach top source snippets for transparency
            issue["source_citations"] = contexts
            issue.setdefault("document", doc_type)
            merged_issues.append(issue)

        # Annotate and save reviewed docx
        base_name, ext = os.path.splitext(os.path.basename(path))
        reviewed_name = f"{base_name}_reviewed{ext}"
        reviewed_path = os.path.join(config.outputs_dir, reviewed_name)
        annotate_docx_with_issues(input_path=path, issues=merged_issues, output_path=reviewed_path)
        reviewed_paths.append(reviewed_path)

        document_analysis.append({
            "file_name": os.path.basename(path),
            "document_type": doc_type,
            "issues_found": merged_issues,
        })

    # Determine process by content (POC: default to Company Incorporation if any known doc)
    process = detect_process_by_content(document_analysis)

    # Checklist verification
    required_set = set(REQUIRED_INCORP_DOCS)
    missing = sorted(list(required_set - present_required_docs))

    summary = {
        "timestamp": now_timestamp_ist(),
        "process": process,
        "documents_uploaded": len(uploaded_paths),
        "required_documents": len(required_set),
        "missing_documents": missing,
        "document_analysis": document_analysis,
    }

    # Save consolidated JSON
    json_name = f"summary_{summary['timestamp'].replace(':', '-')}.json"
    json_path = os.path.join(config.outputs_dir, json_name)
    save_json_pretty(summary, json_path)

    # Also provide a zip of reviewed docs for convenience
    zip_path = os.path.join(config.outputs_dir, f"reviewed_docs_{summary['timestamp'].replace(':', '-')}.zip")
    if reviewed_paths:
        zip_files(reviewed_paths, zip_path)

    human_message = (
        f"Index: {status_msg}\n"
        f"Detected process: {process}\n"
        f"You uploaded {len(uploaded_paths)} document(s). "
        f"Required: {len(required_set)}. Missing: {len(missing)}."
    )

    return summary, reviewed_paths, json_path, zip_path, human_message


def build_ui():
    with gr.Blocks(title="ADGM Corporate Agent") as demo:
        gr.Markdown("**ADGM Corporate Agent** — Upload `.docx` files for review (RAG + rules).")
        with gr.Row():
            files = gr.Files(label="Upload .docx files", file_types=[".docx"], file_count="multiple")
        with gr.Row():
            rebuild = gr.Checkbox(label="Rebuild Index (RAG)", value=False)
        analyze_btn = gr.Button("Analyze")

        with gr.Accordion("Results", open=True):
            resumen = gr.JSON(label="Consolidated Summary JSON (preview)")
            reviewed_files = gr.Files(label="Reviewed DOCX files")
            summary_json = gr.File(label="Download Consolidated JSON")
            reviewed_zip = gr.File(label="Download ZIP of Reviewed DOCX")
            notes = gr.Markdown()

        analyze_btn.click(
            fn=analyze_documents,
            inputs=[files, rebuild],
            outputs=[resumen, reviewed_files, summary_json, reviewed_zip, notes],
        )

    return demo


def main():
    load_dotenv()  # load .env if present
    demo = build_ui()
    demo.launch()


if __name__ == "__main__":
    main()


