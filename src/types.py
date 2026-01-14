"""
共通の型定義

アプリケーション全体で使用する型定義を集約します。
"""
from typing import TypedDict, List, Optional, Dict, Any, Tuple


class PageData(TypedDict):
    """ページデータの型"""
    page: int
    content: str
    metadata: Dict[str, Any]


class ChunkData(TypedDict):
    """チャンクデータの型"""
    content: str
    metadata: Dict[str, Any]


class SearchResult(TypedDict):
    """検索結果の型"""
    content: str
    metadata: Dict[str, Any]
    distance: float
    rerank_score: Optional[float]


class ProcessResult(TypedDict):
    """PDF処理結果の型"""
    success: bool
    message: str
    filename: str
    chunks_count: int


class GenerateAnswerResult(TypedDict):
    """回答生成結果の型"""
    success: bool
    answer: str
    sources: List[Tuple[int, str, str, str, Tuple[str, ...]]]  # (page, source, url, text, chunks)
    error: str


class DBStatus(TypedDict):
    """データベースステータスの型"""
    exists: bool
    document_count: int
    collections: List[str]
    error: Optional[str]


class ChatMessage(TypedDict):
    """チャットメッセージの型"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str]
    sources: Optional[List[Any]]


class MultiplePDFProcessResult(TypedDict):
    """複数PDF処理結果の型"""
    success: bool
    message: str
    results: List[ProcessResult]
    total_chunks: int


class ClearDatabaseResult(TypedDict):
    """データベースクリア結果の型"""
    success: bool
    message: str
