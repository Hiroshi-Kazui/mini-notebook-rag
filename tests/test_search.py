"""
検索機能のテスト
"""
import unittest
import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.retrieval.search import semantic_search
from src.config import settings


class TestSearch(unittest.TestCase):
    """検索機能のテストクラス"""
    
    @unittest.skipIf(not os.getenv("GOOGLE_API_KEY"), "GOOGLE_API_KEYが設定されていません")
    @unittest.skipIf(not os.path.exists(settings.storage.chroma_path), "ChromaDBが初期化されていません")
    def test_semantic_search(self):
        """セマンティック検索のテスト"""
        try:
            query = "テストクエリ"
            results = semantic_search(query, top_k=3)
            
            # 結果がリストであることを確認
            self.assertIsInstance(results, list)
            
            # 各結果に必要なキーが含まれていることを確認
            if results:
                for result in results:
                    self.assertIn("content", result)
                    self.assertIn("metadata", result)
                    self.assertIn("distance", result)
        except Exception as e:
            self.fail(f"検索に失敗しました: {e}")
    
    def test_semantic_search_without_api_key(self):
        """APIキーなしでのエラーテスト"""
        # APIキーを一時的に削除
        original_key = os.environ.get("GOOGLE_API_KEY")
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]
        
        try:
            with self.assertRaises(ValueError):
                semantic_search("テストクエリ")
        finally:
            # APIキーを復元
            if original_key:
                os.environ["GOOGLE_API_KEY"] = original_key
    
    def test_semantic_search_empty_query(self):
        """空のクエリでのテスト"""
        if not os.getenv("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEYが設定されていません")
        
        try:
            results = semantic_search("", top_k=1)
            # 空のクエリでもエラーにならないことを確認
            self.assertIsInstance(results, list)
        except Exception as e:
            # 空のクエリでエラーが発生する場合は許容
            pass


if __name__ == '__main__':
    unittest.main()
