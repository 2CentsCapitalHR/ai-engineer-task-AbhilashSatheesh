from __future__ import annotations
from typing import List, Dict, Any

from src.config import AppConfig

try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # type: ignore

class LLMClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.is_enabled = config.llm_provider != "none"
        self.provider = (config.llm_provider or "none").lower()
        self.client = None  # OpenAI client when provider == openai
        self.gemini_model = None  # Google Generative AI model when provider == gemini
        self.is_ready = False

        if self.is_enabled and self.provider == "openai" and OpenAI is not None:
            kwargs = {}
            if config.openai_base_url:
                kwargs["base_url"] = config.openai_base_url
            self.client = OpenAI(api_key=config.openai_api_key, **kwargs)
            self.is_ready = self.client is not None
        elif self.is_enabled and self.provider == "gemini" and genai is not None and config.google_api_key:
            try:
                genai.configure(api_key=config.google_api_key)
                model_name = config.gemini_model or "gemini-1.5-flash"
                self.gemini_model = genai.GenerativeModel(model_name)
                self.is_ready = self.gemini_model is not None
            except Exception:
                self.is_ready = False

    def analyze_document(self, text: str, doc_type: str, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self.is_enabled or not self.is_ready:
            return []

        system = (
            "You are a legal compliance assistant for ADGM. "
            "Identify ambiguous language, missing clauses, and ADGM non-compliance. "
            "Return compact, actionable issues with severity 'Medium' and concise suggestions."
        )
        ctx_str = "\n\n".join([f"Source: {c.get('source')}\n{c.get('snippet')}" for c in contexts[:5]])
        prompt = (
            f"Document type: {doc_type}\n" \
            f"Context (ADGM references):\n{ctx_str}\n\n" \
            f"Document content (truncated):\n{text[:4000]}\n\n" \
            "List up to 5 issues as JSON with keys: section (if any), issue, severity, suggestion."
        )

        content = "[]"
        try:
            if self.provider == "openai" and self.client is not None:
                resp = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                content = resp.choices[0].message.content or "[]"
            elif self.provider == "gemini" and self.gemini_model is not None:
                # Send system + user prompt as parts
                resp = self.gemini_model.generate_content([system, prompt])
                # Prefer response.text; fallback to first candidate content parts
                if hasattr(resp, "text") and resp.text:
                    content = resp.text
                else:
                    try:
                        content = resp.candidates[0].content.parts[0].text  # type: ignore
                    except Exception:
                        content = "[]"
            else:
                return []
        except Exception:
            return []

        # Robust JSON parsing fallback
        issues: List[Dict[str, Any]] = []
        import json
        try:
            issues = json.loads(content)
        except Exception:
            # try to extract JSON array
            import re
            m = re.search(r"\[[\s\S]*\]", content)
            if m:
                try:
                    issues = json.loads(m.group(0))
                except Exception:
                    issues = []
        for iss in issues:
            iss.setdefault("severity", "Medium")
        return issues


