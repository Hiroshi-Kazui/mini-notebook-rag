import os
import sys
import json
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict

# Windows環境でのエンコーディングエラー対策
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# 設定のインポート
from src.config import settings

def store_embeddings(processed_file: str, storage_path: str = None):
    """
    JSONデータからテキストを読み込み、Google Geminiでベクトル化してChromaDBに保存します。
    
    Args:
        processed_file: 処理済みJSONファイルのパス
        storage_path: ChromaDBの保存パス（Noneの場合は設定から取得）
    """
    if storage_path is None:
        storage_path = settings.storage.chroma_path
    
    api_key = settings.embedding.api_key
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")

    # 1. データ読み込み
    with open(processed_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks from {processed_file}")

    # 2. ChromaDBの初期化
    client = chromadb.PersistentClient(path=storage_path)
    
    # Google Gemini Embedding関数
    gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=api_key,
        model_name=settings.embedding.model,
        task_type=settings.embedding.task_type_document
    )

    # コレクション（テーブルのようなもの）の作成または取得
    collection_name = settings.storage.collection_name
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=gemini_ef,
        metadata={"hnsw:space": "cosine"}
    )

    # 3. データの登録
    ids = [f"{os.path.basename(processed_file)}_{i}" for i in range(len(chunks))]
    documents = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    print(f"Upserting to collection '{collection_name}'...")
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"Successfully stored {len(chunks)} vectors.")

if __name__ == "__main__":
    processed_dir = "data/processed"
    storage_dir = "storage/chroma"
    
    files = [f for f in os.listdir(processed_dir) if f.endswith(".json")]
    
    if not files:
        print(f"No processed files found in {processed_dir}.")
    else:
        for file_name in files:
            file_path = os.path.join(processed_dir, file_name)
            print(f"Processing: {file_name}")
            try:
                store_embeddings(file_path, storage_dir)
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
