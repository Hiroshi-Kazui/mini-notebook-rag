import os
import sys
from typing import List, Dict
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Windows環境でのエンコーディングエラー対策
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# 設定のインポート
from src.config import settings

def semantic_search(query: str, storage_path: str = None, top_k: int = None) -> List[Dict]:
    """
    ベクトル検索を実行し、結果を辞書のリストとして返す

    Args:
        query: 検索クエリ
        storage_path: ChromaDBの保存パス（Noneの場合は設定から取得）
        top_k: 取得する結果の件数（Noneの場合は設定から取得）

    Returns:
        検索結果のリスト（各要素は content, metadata, distance を含む辞書）
    """
    if storage_path is None:
        storage_path = settings.storage.chroma_path
    if top_k is None:
        top_k = settings.retrieval.default_top_k
    
    api_key = settings.embedding.api_key
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")

    # ChromaDBの初期化
    client = chromadb.PersistentClient(path=storage_path)

    # Google Gemini Embedding関数
    gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=api_key,
        model_name=settings.embedding.model,
        task_type=settings.embedding.task_type_query
    )

    collection_name = settings.storage.collection_name
    collection = client.get_collection(
        name=collection_name,
        embedding_function=gemini_ef
    )

    # 検索実行
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    # 結果を整形
    search_results = []
    for i in range(len(results["documents"][0])):
        search_results.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return search_results


def search_db(query: str, storage_path: str, n_results: int = 3, use_reranking: bool = False,
              initial_k: int = 100, final_k: int = 20):
    """
    クエリに対して類似度の高いチャンクをベクトルDBから検索します。

    Args:
        query: 検索クエリ
        storage_path: ChromaDBの保存パス
        n_results: 最終的に表示する結果の件数
        use_reranking: LLMリランキングを使用するかどうか
        initial_k: リランキング使用時の初期取得件数
        final_k: リランキング後に残す件数
    """
    if use_reranking:
        # リランキングを使用する場合
        from reranker import rerank_with_llm

        # まず広めに取得
        initial_results = semantic_search(query, storage_path, top_k=initial_k)

        # LLMでリランキング
        reranked_results = rerank_with_llm(query, initial_results, top_k=final_k)

        results_to_show = reranked_results[:n_results]

        print(f"\n🔍 Query: {query}")
        print(f"📊 初期取得: {len(initial_results)}件 → リランキング後: {len(reranked_results)}件 → 表示: {len(results_to_show)}件")
        print("-" * 50)

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
        # 通常のベクトル検索のみ
        results = semantic_search(query, storage_path, top_k=n_results)

        print(f"\n🔍 Query: {query}")
        print("-" * 50)

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

    # テスト用のクエリ
    sample_queries = [
        "イエスは心に響く教え方ができました。どうしてですか",
        "ナアマンから何を学べますか",
        "エホバを信頼することの大切さ"
    ]

    print("=" * 80)
    print("通常のベクトル検索（上位3件）")
    print("=" * 80)

    for q in sample_queries:
        try:
            search_db(q, storage_dir, n_results=3, use_reranking=False)
        except Exception as e:
            print(f"Error searching for '{q}': {e}")

    print("\n\n")
    print("=" * 80)
    print("LLMリランキングを使用した検索（初期100件 → 上位20件 → 表示3件）")
    print("=" * 80)

    for q in sample_queries:
        try:
            search_db(q, storage_dir, n_results=3, use_reranking=True, initial_k=100, final_k=20)
        except Exception as e:
            print(f"Error searching for '{q}': {e}")
