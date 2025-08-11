import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    project_root: str
    data_reference_dir: str
    outputs_dir: str
    vectorstore_dir: str

    llm_provider: str
    openai_api_key: str | None
    openai_base_url: str | None
    google_api_key: str | None
    gemini_model: str

    embeddings_provider: str
    embeddings_model: str

    timezone: str

    @staticmethod
    def from_env() -> "AppConfig":
        cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = cwd
        data_reference_dir = os.path.join(project_root, "data", "reference")
        outputs_dir = os.path.join(project_root, "outputs")
        vectorstore_dir = os.path.join(project_root, "vectorstore")

        llm_provider = os.getenv("LLM_PROVIDER", "none").lower()
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_base_url = os.getenv("OPENAI_BASE_URL")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        embeddings_provider = os.getenv("EMBEDDINGS_PROVIDER", "hf").lower()
        embeddings_model = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

        timezone = os.getenv("TIMEZONE", "Asia/Kolkata")

        return AppConfig(
            project_root=project_root,
            data_reference_dir=data_reference_dir,
            outputs_dir=outputs_dir,
            vectorstore_dir=vectorstore_dir,
            llm_provider=llm_provider,
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            google_api_key=google_api_key,
            gemini_model=gemini_model,
            embeddings_provider=embeddings_provider,
            embeddings_model=embeddings_model,
            timezone=timezone,
        )


