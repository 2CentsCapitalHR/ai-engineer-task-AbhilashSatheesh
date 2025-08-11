## ADGM Corporate Agent (Gradio)

An AI-powered Corporate Agent to review ADGM incorporation documents with document intelligence:
- Accepts `.docx` uploads
- Auto-detects process and document types
- Checks completeness against an ADGM incorporation checklist
- Detects red flags (jurisdiction, signatures, placeholders, clause gaps)
- Uses RAG (Chroma) with source-citation snippets
- Produces an annotated `.docx` (highlights + review notes) and a consolidated JSON report

### Quick Start

1) Create and activate a virtual environment (optional but recommended)

```powershell
py -m venv .venv
. .venv\\Scripts\\Activate.ps1
```

2) Install dependencies

```powershell
pip install -r requirements.txt
```

3) Configure environment

- Copy `.env.example` to `.env` and set keys as needed. By default, the app uses local HF embeddings and does not require an API key. If you want LLM generation:
  - For OpenAI, set `LLM_PROVIDER=openai` and `OPENAI_API_KEY=...` (or point to an OpenAI-compatible base URL).
  - For Gemini, set `LLM_PROVIDER=gemini` and `GOOGLE_API_KEY=...` (optionally `GEMINI_MODEL`, default `gemini-1.5-flash`).

4) Add reference materials

- Place ADGM reference files under `data/reference/` (PDF, DOCX, or TXT). The vector index will be built automatically on first run. You can click "Rebuild Index" to refresh.

5) Run the app

```powershell
python app.py
```

Open the printed local URL in your browser. Upload one or more `.docx` files and click Analyze.

### Outputs

- Reviewed `.docx` files saved under `outputs/` with suffix `_reviewed.docx`
- Consolidated JSON saved under `outputs/` (includes timestamp, process, checklist summary, and per-document findings)

### Configuration

- `LLM_PROVIDER`: `openai`, `gemini`, or `none` (default `none`).
- `OPENAI_API_KEY`: required if using OpenAI.
- `OPENAI_BASE_URL`: optional; set this to use an OpenAI-compatible free endpoint.
- `GOOGLE_API_KEY`: required if using Gemini.
- `GEMINI_MODEL`: optional Gemini model id (default `gemini-1.5-flash`).
- `EMBEDDINGS_PROVIDER`: `hf` (default) or `openai`.
- `EMBEDDINGS_MODEL`: HF model id (default `sentence-transformers/all-MiniLM-L6-v2`).

### Project Structure

```
adgm_corporate_agent/
  app.py
  requirements.txt
  README.md
  .env.example
  data/
    reference/
  outputs/
  vectorstore/
  src/
    config.py
    llm/
      client.py
    rag/
      embeddings.py
      indexer.py
      retriever.py
    rules/
      checks.py
    docx_tools/
      parser.py
      annotator.py
    utils/
      file_utils.py
      time_utils.py
```

### Notes

- Annotation uses text highlights and an appended "Review Notes" section (no Word XML comments) for broad compatibility.
- Document classification and red-flag checks are primarily rule-based with optional LLM assistance.
- Only the Company Incorporation process is fully implemented in this POC.

### License

MIT


