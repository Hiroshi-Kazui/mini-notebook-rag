import unittest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ingestion.extract import extract_text_from_pdf


class TestExtract(unittest.TestCase):
    """PDF抽出機能のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.test_pdf_path = "data/raw/w_J_202603.pdf"

    def test_extract_text_from_pdf_exists(self):
        """PDFファイルが存在する場合のテスト"""
        if not os.path.exists(self.test_pdf_path):
            self.skipTest(f"テストPDFが見つかりません: {self.test_pdf_path}")

        result = extract_text_from_pdf(self.test_pdf_path)

        # 結果がリストであることを確認
        self.assertIsInstance(result, list)

        # 少なくとも1ページ以上あることを確認
        self.assertGreater(len(result), 0)

        # 各ページに必要なキーがあることを確認
        for page_data in result:
            self.assertIn('page', page_data)
            self.assertIn('content', page_data)
            self.assertIn('metadata', page_data)

    def test_extract_text_from_nonexistent_pdf(self):
        """存在しないPDFファイルのテスト"""
        nonexistent_path = "nonexistent_file.pdf"

        with self.assertRaises(Exception):
            extract_text_from_pdf(nonexistent_path)


if __name__ == '__main__':
    unittest.main()
