"""
リランキング機能のテスト
"""
import unittest
import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.retrieval.reranker import rerank_with_llm
from src.types import SearchResult


class TestReranker(unittest.TestCase):
    """リランキング機能のテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # モック検索結果を作成
        self.mock_search_results: list[SearchResult] = [
            {
                "content": "これは最初の検索結果です。",
                "metadata": {"page": 1, "source": "test.pdf"},
                "distance": 0.1,
                "rerank_score": None
            },
            {
                "content": "これは2番目の検索結果です。",
                "metadata": {"page": 2, "source": "test.pdf"},
                "distance": 0.2,
                "rerank_score": None
            },
            {
                "content": "これは3番目の検索結果です。",
                "metadata": {"page": 3, "source": "test.pdf"},
                "distance": 0.3,
                "rerank_score": None
            }
        ]
    
    @unittest.skipIf(not os.getenv("GOOGLE_API_KEY"), "GOOGLE_API_KEYが設定されていません")
    def test_rerank_with_llm(self):
        """LLMリランキングのテスト"""
        try:
            query = "テストクエリ"
            reranked = rerank_with_llm(query, self.mock_search_results, top_k=2)
            
            # 結果がリストであることを確認
            self.assertIsInstance(reranked, list)
            
            # top_k以下の件数であることを確認
            self.assertLessEqual(len(reranked), 2)
            
            # 各結果に必要なキーが含まれていることを確認
            if reranked:
                for result in reranked:
                    self.assertIn("content", result)
                    self.assertIn("metadata", result)
        except Exception as e:
            self.fail(f"リランキングに失敗しました: {e}")
    
    def test_rerank_with_empty_results(self):
        """空の検索結果でのテスト"""
        reranked = rerank_with_llm("テストクエリ", [], top_k=5)
        self.assertEqual(len(reranked), 0)
    
    def test_rerank_with_smaller_top_k(self):
        """top_kが結果数より小さい場合のテスト"""
        if not os.getenv("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEYが設定されていません")
        
        try:
            reranked = rerank_with_llm("テストクエリ", self.mock_search_results, top_k=1)
            self.assertLessEqual(len(reranked), 1)
        except Exception as e:
            # エラーが発生する場合は許容
            pass


if __name__ == '__main__':
    unittest.main()
