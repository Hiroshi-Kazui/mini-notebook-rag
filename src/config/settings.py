"""Application settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class AppSettings:
    """General app settings."""
    name: str = "Mini-Notebook RAG"
    version: str = "1.0.0"
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    max_chat_history: int = int(os.getenv("MAX_CHAT_HISTORY", "50"))
    max_notebooks_per_user: int = int(os.getenv("MAX_NOTEBOOKS_PER_USER", "10"))
    default_notebook_name: str = os.getenv("DEFAULT_NOTEBOOK_NAME", "Default Notebook")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


class EmbeddingSettings:
    """Embedding settings."""
    model: str = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
    api_key: str = os.getenv("GOOGLE_API_KEY", "")
    task_type_document: str = "RETRIEVAL_DOCUMENT"
    task_type_query: str = "RETRIEVAL_QUERY"

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set. Please set it in your .env file.")


class GenerationSettings:
    """Generation settings."""
    model: str = os.getenv("GENERATION_MODEL", "models/gemini-flash-latest")
    temperature: float = float(os.getenv("GENERATION_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("GENERATION_MAX_TOKENS", "2048"))


class RetrievalSettings:
    """Retrieval settings."""
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "3"))
    default_initial_k: int = int(os.getenv("DEFAULT_INITIAL_K", "100"))
    default_final_k: int = int(os.getenv("DEFAULT_FINAL_K", "20"))
    reranking_enabled: bool = os.getenv("RERANKING_ENABLED", "true").lower() == "true"


class StorageSettings:
    """Storage settings."""

    def __init__(self):
        self.chroma_path: str = os.getenv("CHROMA_STORAGE_PATH", "storage/chroma")
        self.collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "notebook_rag_collection")
        self.chat_history_path: str = os.getenv("CHAT_HISTORY_PATH", "storage/chat_history.json")
        self.notebook_metadata_file: str = os.getenv("NOTEBOOK_METADATA_FILE", "storage/notebooks.json")
        self.chat_history_dir: str = os.getenv("CHAT_HISTORY_DIR", "storage/chat_history")
        self.data_raw_dir: str = os.getenv("DATA_RAW_DIR", "data/raw")
        self.data_processed_dir: str = os.getenv("DATA_PROCESSED_DIR", "data/processed")
        self.pdf_server_base_url: str = os.getenv("PDF_SERVER_BASE_URL", "http://localhost:80")

        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
        Path(self.chat_history_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.data_raw_dir).mkdir(parents=True, exist_ok=True)
        Path(self.data_processed_dir).mkdir(parents=True, exist_ok=True)
        Path(self.notebook_metadata_file).parent.mkdir(parents=True, exist_ok=True)
        Path(self.chat_history_dir).mkdir(parents=True, exist_ok=True)


class Settings:
    """Top-level settings container."""

    def __init__(self):
        self.app = AppSettings()
        self.embedding = EmbeddingSettings()
        self.generation = GenerationSettings()
        self.retrieval = RetrievalSettings()
        self.storage = StorageSettings()
        self._ensure_directories()

    def _ensure_directories(self):
        Path(self.storage.chroma_path).mkdir(parents=True, exist_ok=True)
        Path(self.storage.chat_history_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.storage.data_raw_dir).mkdir(parents=True, exist_ok=True)
        Path(self.storage.data_processed_dir).mkdir(parents=True, exist_ok=True)
        Path(self.storage.notebook_metadata_file).parent.mkdir(parents=True, exist_ok=True)
        Path(self.storage.chat_history_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()
