import os
import sys
import json
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Windows encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

from src.config import settings


def _get_collection(storage_path: str):
    api_key = settings.embedding.api_key
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")

    client = chromadb.PersistentClient(path=storage_path)
    gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=api_key,
        model_name=settings.embedding.model,
        task_type=settings.embedding.task_type_document,
    )
    collection_name = settings.storage.collection_name
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=gemini_ef,
        metadata={"hnsw:space": "cosine"},
    )


def store_embeddings(processed_file: str, storage_path: str = None, notebook_id: str = "default"):
    """
    Store processed chunks into ChromaDB with notebook metadata.
    """
    if storage_path is None:
        storage_path = settings.storage.chroma_path

    with open(processed_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    collection = _get_collection(storage_path)

    basename = os.path.basename(processed_file)
    ids = [f"{notebook_id}_{basename}_{i}" for i in range(len(chunks))]
    documents = [c["content"] for c in chunks]
    metadatas = []
    for c in chunks:
        meta = c["metadata"].copy()
        meta["notebook_id"] = notebook_id
        metadatas.append(meta)

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def add_notebook_id_to_existing_chunks(notebook_id: str = "default", storage_path: str = None) -> int:
    """Add notebook_id to existing chunks that don't have it."""
    if storage_path is None:
        storage_path = settings.storage.chroma_path

    collection = _get_collection(storage_path)
    results = collection.get(include=["metadatas", "documents", "ids"])
    metadatas = results.get("metadatas", [])
    ids = results.get("ids", [])
    documents = results.get("documents", [])

    if not ids:
        return 0

    updated_ids = []
    updated_metas = []
    updated_docs = []
    for idx, meta in enumerate(metadatas):
        if not meta or "notebook_id" not in meta:
            new_meta = (meta or {}).copy()
            new_meta["notebook_id"] = notebook_id
            updated_ids.append(ids[idx])
            updated_metas.append(new_meta)
            updated_docs.append(documents[idx])

    if updated_ids:
        collection.upsert(ids=updated_ids, documents=updated_docs, metadatas=updated_metas)
    return len(updated_ids)


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

