"""
アプリケーション設定の一元管理

環境変数から設定を読み込み、アプリケーション全体で使用する設定値を管理します。
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class AppSettings:
    """アプリケーション基本設定"""
    name: str = "Mini-Notebook RAG"
    version: str = "1.0.0"
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    max_chat_history: int = int(os.getenv("MAX_CHAT_HISTORY", "50"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


class EmbeddingSettings:
    """埋め込み設定"""
    model: str = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
    api_key: str = os.getenv("GOOGLE_API_KEY", "")
    task_type_document: str = "RETRIEVAL_DOCUMENT"
    task_type_query: str = "RETRIEVAL_QUERY"
    
    def __post_init__(self):
        """APIキーの検証"""
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEYが設定されていません。.envファイルを確認してください。")


class GenerationSettings:
    """生成モデル設定"""
    model: str = os.getenv("GENERATION_MODEL", "models/gemini-flash-latest")
    temperature: float = float(os.getenv("GENERATION_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("GENERATION_MAX_TOKENS", "2048"))


class RetrievalSettings:
    """検索設定"""
    default_top_k: int = int(os.getenv("DEFAULT_TOP_K", "3"))
    default_initial_k: int = int(os.getenv("DEFAULT_INITIAL_K", "100"))
    default_final_k: int = int(os.getenv("DEFAULT_FINAL_K", "20"))
    reranking_enabled: bool = os.getenv("RERANKING_ENABLED", "true").lower() == "true"


class StorageSettings:
    """ストレージ設定"""
    def __init__(self):
        self.chroma_path: str = os.getenv("CHROMA_STORAGE_PATH", "storage/chroma")
        self.collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "notebook_rag_collection")
        self.chat_history_path: str = os.getenv("CHAT_HISTORY_PATH", "storage/chat_history.json")
        self.data_raw_dir: str = os.getenv("DATA_RAW_DIR", "data/raw")
        self.data_processed_dir: str = os.getenv("DATA_PROCESSED_DIR", "data/processed")
        self.static_dir: str = os.getenv("STATIC_DIR", "static")
        
        # ディレクトリの作成
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
        Path(self.chat_history_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.data_raw_dir).mkdir(parents=True, exist_ok=True)
        Path(self.data_processed_dir).mkdir(parents=True, exist_ok=True)
        Path(self.static_dir).mkdir(parents=True, exist_ok=True)


class Settings:
    """全体設定クラス"""
    def __init__(self):
        self.app = AppSettings()
        self.embedding = EmbeddingSettings()
        self.generation = GenerationSettings()
        self.retrieval = RetrievalSettings()
        self.storage = StorageSettings()
        
        # ディレクトリの初期化
        self._ensure_directories()
    
    def _ensure_directories(self):
        """必要なディレクトリを作成"""
        Path(self.storage.chroma_path).mkdir(parents=True, exist_ok=True)
        Path(self.storage.chat_history_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.storage.data_raw_dir).mkdir(parents=True, exist_ok=True)
        Path(self.storage.data_processed_dir).mkdir(parents=True, exist_ok=True)
        Path(self.storage.static_dir).mkdir(parents=True, exist_ok=True)


# グローバル設定インスタンス
settings = Settings()
