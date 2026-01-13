"""
data/raw にある PDF を直接読み込んでベクトルDB を構築
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ingestion.extract import extract_text_from_pdf
from src.ingestion.chunking import chunk_text
from src.embedding.store import store_embeddings

load_dotenv()

def build_vector_db():
    """data/raw の PDF からベクトルDB を構築"""
    
    raw_dir = "data/raw"
    storage_path = "storage/chroma"
    
    # data/raw 内の PDF ファイルを検索
    pdf_files = list(Path(raw_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ {raw_dir} に PDF ファイルが見つかりません")
        return False
    
    pdf_path = pdf_files[0]
    print(f"📄 PDF を処理中: {pdf_path}")
    
    # 1. PDF からテキスト抽出
    print("\n1. テキスト抽出中...")
    pages = extract_text_from_pdf(str(pdf_path))
    print(f"   ✓ {len(pages)} ページを抽出")
    
    # 2. チャンク分割
    print("\n2. チャンク分割中...")
    chunks = chunk_text(pages, chunk_size=500)
    print(f"   ✓ {len(chunks)} チャンクを生成")
    
    # 3. ベクトルDB に保存
    print("\n3. ベクトルDB に保存中...")
    print("   （この処理には時間がかかります...）")
    
    # ChromaDB に直接保存
    import chromadb
    from chromadb.utils import embedding_functions
    import google.generativeai as genai
    
    # ChromaDB クライアント作成
    client = chromadb.PersistentClient(path=storage_path)
    
    # コレクション作成または取得
    try:
        collection = client.get_collection(name="pdf_documents")
        print("   既存のコレクションを使用")
    except:
        # Gemini 埋め込み関数
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        
        class GoogleGenerativeAiEmbeddingFunction(embedding_functions.EmbeddingFunction):
            def __call__(self, input: list[str]) -> list[list[float]]:
                embeddings = []
                for text in input:
                    result = genai.embed_content(
                        model="models/text-embedding-004",
                        content=text,
                        task_type="RETRIEVAL_DOCUMENT"
                    )
                    embeddings.append(result['embedding'])
                return embeddings
        
        gemini_ef = GoogleGenerativeAiEmbeddingFunction()
        collection = client.create_collection(
            name="pdf_documents",
            embedding_function=gemini_ef,
            metadata={"hnsw:space": "cosine"}
        )
        print("   新しいコレクションを作成")
    
    # チャンクを追加
    documents = [chunk["content"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"\n✅ ベクトルDB の構築が完了しました")
    print(f"   - チャンク数: {len(chunks)}")
    print(f"   - 保存先: {storage_path}")
    return True

if __name__ == "__main__":
    print("=" * 80)
    print("ベクトルDB 構築スクリプト")
    print("=" * 80)
    
    success = build_vector_db()
    
    if success:
        print("\n次のステップ:")
        print("  python debug_search.py  # 検索品質を確認")
    
    sys.exit(0 if success else 1)
