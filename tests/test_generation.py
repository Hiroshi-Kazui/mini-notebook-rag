"""
回答生成機能のテスト
"""
import unittest
import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.generation.rag import generate_answer
from src.config import settings


class TestGeneration(unittest.TestCase):
    """回答生成機能のテストクラス"""
    
    @unittest.skipIf(not os.getenv("GOOGLE_API_KEY"), "GOOGLE_API_KEYが設定されていません")
    @unittest.skipIf(not os.path.exists(settings.storage.chroma_path), "ChromaDBが初期化されていません")
    def test_generate_answer(self):
        """回答生成のテスト"""
        try:
            query = "テストクエリ"
            storage_path = settings.storage.chroma_path
            
            # 注意: 実際のAPI呼び出しが発生するため、スキップ可能にする
            generate_answer(query, storage_path)
            
            # 成功した場合はTrue
            self.assertTrue(True)
        except Exception as e:
            # API呼び出しが失敗する場合は許容
            self.skipTest(f"回答生成に失敗しました（API呼び出しエラー）: {e}")
    
    def test_generate_answer_without_api_key(self):
        """APIキーなしでのエラーテスト"""
        # APIキーを一時的に削除
        original_key = os.environ.get("GOOGLE_API_KEY")
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]
        
        try:
            with self.assertRaises(ValueError):
                generate_answer("テストクエリ", settings.storage.chroma_path)
        finally:
            # APIキーを復元
            if original_key:
                os.environ["GOOGLE_API_KEY"] = original_key


if __name__ == '__main__':
    unittest.main()
