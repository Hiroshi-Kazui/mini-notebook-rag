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

def store_embeddings(processed_file: str, storage_path: str):
    """
    JSONデータからテキストを読み込み、Google Geminiでベクトル化してChromaDBに保存します。
    """
    api_key = os.getenv("GOOGLE_API_KEY")
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
        model_name="models/text-embedding-004",
        task_type="RETRIEVAL_DOCUMENT"
    )

    # コレクション（テーブルのようなもの）の作成または取得
    collection_name = "notebook_rag_collection"
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
