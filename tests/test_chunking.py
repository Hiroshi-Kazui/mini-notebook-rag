import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ingestion.chunking import chunk_text


class TestChunking(unittest.TestCase):
    """テキストチャンク化機能のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.sample_data = [
            {
                'page': 1,
                'content': '吾輩は猫である。名前はまだ無い。どこで生れたかとんと見当がつかぬ。' * 20,
                'metadata': {'source': 'test.pdf'}
            },
            {
                'page': 2,
                'content': 'これはテストデータです。' * 30,
                'metadata': {'source': 'test.pdf'}
            }
        ]

    def test_chunk_text_basic(self):
        """基本的なチャンク化のテスト"""
        chunks = chunk_text(self.sample_data, chunk_size=500, chunk_overlap=50)

        # 結果がリストであることを確認
        self.assertIsInstance(chunks, list)

        # チャンクが生成されることを確認
        self.assertGreater(len(chunks), 0)

        # 各チャンクに必要なキーがあることを確認
        for chunk in chunks:
            self.assertIn('content', chunk)
            self.assertIn('metadata', chunk)
            self.assertIn('page', chunk['metadata'])
            self.assertIn('chunk_id', chunk['metadata'])

    def test_chunk_text_size(self):
        """チャンクサイズのテスト"""
        chunk_size = 200
        chunks = chunk_text(self.sample_data, chunk_size=chunk_size, chunk_overlap=20)

        # ほとんどのチャンクがサイズ制限内であることを確認
        for chunk in chunks:
            # オーバーラップを考慮して、少し余裕を持たせる
            self.assertLessEqual(len(chunk['content']), chunk_size * 1.5)

    def test_chunk_text_empty_input(self):
        """空の入力のテスト"""
        chunks = chunk_text([])

        # 空のリストが返されることを確認
        self.assertEqual(len(chunks), 0)


if __name__ == '__main__':
    unittest.main()
