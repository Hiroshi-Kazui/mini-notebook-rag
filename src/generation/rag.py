import os
import sys
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
from dotenv import load_dotenv

# Windows環境でのエンコーディングエラー対策
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

def generate_answer(query: str, storage_path: str):
    """
    RAGパイプライン：検索 -> 構築 -> 生成
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")

    # 1. 検索 (Retrieval)
    client = chromadb.PersistentClient(path=storage_path)
    gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=api_key,
        model_name="models/text-embedding-004",
        task_type="RETRIEVAL_QUERY"
    )
    collection = client.get_collection(
        name="notebook_rag_collection",
        embedding_function=gemini_ef
    )
    
    results = collection.query(query_texts=[query], n_results=20)
    
    # 2. プロンプト構築
    context = ""
    sources = []
    for i in range(len(results["documents"][0])):
        context += f"\n--- 資料 {i+1} ---\n{results['documents'][0][i]}\n"
        sources.append(f"P{results['metadatas'][0][i]['page']} ({results['metadatas'][0][i]['source']})")

    prompt = f"""
あなたは提供された資料に基づいて質問に答える、誠実で役立つアシスタントです。
以下の資料（コンテキスト）の内容のみを使用して、ユーザーの質問に日本語で詳しく答えてください。
回答の際には、どの資料に基づいた情報かを明記してください（例: [資料 1]）。
もし資料に答えが含まれていない場合は、「提供された資料にはその情報が含まれていません」と正直に答えてください。

【資料】
{context}

【ユーザーの質問】
{query}
"""

    # 3. 生成 (Generation)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    print(f"\n🤔 質問: {query}")
    print("生成中...")
    
    response = model.generate_content(prompt)
    
    print("\n✨ 回答:")
    print("-" * 50)
    print(response.text)
    print("-" * 50)
    print("📍 参照箇所:", ", ".join(list(set(sources))))

if __name__ == "__main__":
    storage_dir = "storage/chroma"
    
    # テスト用のクエリ
    test_query = "ナアマンから何を学べますか？"
    
    try:
        generate_answer(test_query, storage_dir)
    except Exception as e:
        print(f"Error: {e}")
