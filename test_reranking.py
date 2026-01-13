"""
リランキング機能のテストスクリプト
質問に対する検索結果を確認し、改善が必要か判定
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ui.streamlit_helpers import generate_answer_ui

load_dotenv()

def test_reranking():
    """リランキング機能をテスト"""
    
    query = "イエスは心に響く教え方ができました。どうしてですか"
    
    print("=" * 80)
    print(f"質問: {query}")
    print("=" * 80)
    
    # RAG で回答生成
    print("\n回答生成中...")
    result = generate_answer_ui(query, n_results=20)
    
    if not result['success']:
        print(f"\n❌ エラー: {result['error']}")
        return False
    
    print(f"\n【回答】")
    print(result['answer'])
    
    print(f"\n【参照ソース】")
    for i, source in enumerate(result['sources'], 1):
        if isinstance(source, tuple) and len(source) >= 4:
            page, src_file, url, text, *_ = source
            print(f"{i}. ページ {page}")
        else:
            print(f"{i}. {source}")
    
    # 評価: ページ3が含まれているか
    page_3_found = False
    for source in result['sources']:
        if isinstance(source, tuple) and len(source) >= 2:
            if source[0] == 3:  # page
                page_3_found = True
                break
    
    print("\n" + "=" * 80)
    if page_3_found:
        print("✅ 成功: ページ3（正解）が参照ソースに含まれています")
        return True
    else:
        print("❌ 失敗: ページ3（正解）が参照ソースに含まれていません")
        print("\n改善が必要です。")
        return False

if __name__ == "__main__":
    success = test_reranking()
    sys.exit(0 if success else 1)
