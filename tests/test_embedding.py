"""
埋め込み機能のテスト
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.embedding.store import store_embeddings
from src.config import settings


class TestEmbedding(unittest.TestCase):
    """埋め込み機能のテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.test_storage_path = os.path.join(self.temp_dir, "test_chroma")
        self.test_processed_dir = os.path.join(self.temp_dir, "processed")
        os.makedirs(self.test_processed_dir, exist_ok=True)
        
        # テスト用のJSONファイルを作成
        self.test_json = os.path.join(self.test_processed_dir, "test.json")
        test_data = [
            {
                "content": "これはテスト用のチャンクです。",
                "metadata": {
                    "page": 1,
                    "source": "test.pdf",
                    "chunk_id": 0
                }
            },
            {
                "content": "2つ目のテストチャンクです。",
                "metadata": {
                    "page": 1,
                    "source": "test.pdf",
                    "chunk_id": 1
                }
            }
        ]
        import json
        with open(self.test_json, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipIf(not os.getenv("GOOGLE_API_KEY"), "GOOGLE_API_KEYが設定されていません")
    def test_store_embeddings(self):
        """埋め込み保存のテスト"""
        try:
            store_embeddings(self.test_json, self.test_storage_path)
            # 成功した場合はTrue
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"埋め込み保存に失敗しました: {e}")
    
    def test_store_embeddings_without_api_key(self):
        """APIキーなしでのエラーテスト"""
        # APIキーを一時的に削除
        original_key = os.environ.get("GOOGLE_API_KEY")
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]
        
        try:
            with self.assertRaises(ValueError):
                store_embeddings(self.test_json, self.test_storage_path)
        finally:
            # APIキーを復元
            if original_key:
                os.environ["GOOGLE_API_KEY"] = original_key


if __name__ == '__main__':
    unittest.main()
