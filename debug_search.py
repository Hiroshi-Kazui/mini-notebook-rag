"""
ベクトルDB の検索結果をデバッグするスクリプト
API リクエストを最小限に抑えながら、検索品質を確認
"""
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

# ChromaDB に接続
client = chromadb.PersistentClient(path="storage/chroma")
collection = client.get_collection(name="pdf_documents")

# クエリ: 「イエスは心に響く教え方ができました。どうしてですか」
query = "イエスは心に響く教え方ができました。どうしてですか"

print(f"クエリ: {query}\n")
print("=" * 80)

# Gemini の埋め込みを使用して検索（API リクエスト 1回のみ）
import google.generativeai as genai
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# クエリの埋め込みを生成
result = genai.embed_content(
    model="models/text-embedding-004",
    content=query,
    task_type="RETRIEVAL_QUERY"
)
query_embedding = result['embedding']

# ChromaDB で検索（API リクエストなし、ローカル検索のみ）
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=20
)

print(f"\n検索結果: {len(results['documents'][0])} 件\n")

# 上位10件の結果を表示
for i in range(min(10, len(results['documents'][0]))):
    distance = results['distances'][0][i]
    page = results['metadatas'][0][i].get('page', '不明')
    source = results['metadatas'][0][i].get('source', '不明')
    chunk = results['documents'][0][i][:200]  # 最初の200文字
    
    print(f"\n【結果 {i+1}】")
    print(f"  距離: {distance:.6f}")
    print(f"  ページ: {page}")
    print(f"  ソース: {source}")
    print(f"  内容: {chunk}...")
    print("-" * 80)

# PDF 3ページ目の内容が含まれているか確認
print("\n\n【PDF 3ページ目の検索】")
print("=" * 80)

# ページ3のチャンクを直接検索
all_data = collection.get()
page_3_chunks = []
for i, metadata in enumerate(all_data['metadatas']):
    if metadata.get('page') == 3:
        page_3_chunks.append({
            'id': all_data['ids'][i],
            'content': all_data['documents'][i][:200],
            'metadata': metadata
        })

print(f"\nページ3のチャンク数: {len(page_3_chunks)}")
for i, chunk in enumerate(page_3_chunks[:5]):
    print(f"\n【ページ3 チャンク {i+1}】")
    print(f"  ID: {chunk['id']}")
    print(f"  内容: {chunk['content']}...")
    print("-" * 80)

print("\n\n総API リクエスト数: 1回（埋め込み生成のみ）")
