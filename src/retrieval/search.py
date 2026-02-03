import sys
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

from src.config import settings


def semantic_search(
    query: str,
    storage_path: str = None,
    top_k: int = None,
    notebook_id: Optional[str] = None,
) -> List[Dict]:
    if storage_path is None:
        storage_path = settings.storage.chroma_path
    if top_k is None:
        top_k = settings.retrieval.default_top_k

    api_key = settings.embedding.api_key
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")

    client = chromadb.PersistentClient(path=storage_path)
    gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=api_key,
        model_name=settings.embedding.model,
        task_type=settings.embedding.task_type_query,
    )

    collection = client.get_collection(
        name=settings.storage.collection_name,
        embedding_function=gemini_ef,
    )

    where_filter = {"notebook_id": notebook_id} if notebook_id else None
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where_filter,
    )

    search_results = []
    for i in range(len(results["documents"][0])):
        search_results.append(
            {
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )

    return search_results


def search_db(
    query: str,
    storage_path: str,
    n_results: int = 3,
    use_reranking: bool = False,
    initial_k: int = 100,
    final_k: int = 20,
    notebook_id: Optional[str] = None,
):
    if use_reranking:
        from reranker import rerank_with_llm

        initial_results = semantic_search(
            query, storage_path, top_k=initial_k, notebook_id=notebook_id
        )
        reranked_results = rerank_with_llm(query, initial_results, top_k=final_k)
        results_to_show = reranked_results[:n_results]

        for i, result in enumerate(results_to_show, 1):
            doc = result["content"]
            meta = result["metadata"]
            dist = result.get("distance", 0)
            rerank_score = result.get("rerank_score", "N/A")

            print(f"Result {i} (Distance: {dist:.4f}, Rerank Score: {rerank_score})")
            print(f"Source: {meta['source']} (Page {meta['page']})")
            print(f"Content: {doc[:300]}...")
            print("-" * 50)
    else:
        results = semantic_search(
            query, storage_path, top_k=n_results, notebook_id=notebook_id
        )

        for i, result in enumerate(results, 1):
            doc = result["content"]
            meta = result["metadata"]
            dist = result["distance"]

            print(f"Result {i} (Distance: {dist:.4f})")
            print(f"Source: {meta['source']} (Page {meta['page']})")
            print(f"Content: {doc[:300]}...")
            print("-" * 50)


if __name__ == "__main__":
    storage_dir = "storage/chroma"
    sample_queries = [
        "日本の建築基準法の概要を教えて",
        "ハードウェア設計のポイントは？",
        "エンジニアのキャリアについて",
    ]

    for q in sample_queries:
        try:
            search_db(q, storage_dir, n_results=3, use_reranking=False)
        except Exception as e:
            print(f"Error searching for '{q}': {e}")

