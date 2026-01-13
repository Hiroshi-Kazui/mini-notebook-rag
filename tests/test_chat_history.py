import unittest
import sys
import os
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.chat_history import ChatHistoryManager


class TestChatHistory(unittest.TestCase):
    """チャット履歴管理のテスト"""

    def setUp(self):
        """テストのセットアップ"""
        # テンポラリファイルを使用
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.manager = ChatHistoryManager(history_file=self.temp_file.name, max_messages=10)

    def tearDown(self):
        """テストのクリーンアップ"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_add_message(self):
        """メッセージ追加のテスト"""
        self.manager.add_message('user', 'こんにちは')
        messages = self.manager.load_history()

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['role'], 'user')
        self.assertEqual(messages[0]['content'], 'こんにちは')
        self.assertIn('timestamp', messages[0])

    def test_add_message_with_sources(self):
        """ソース付きメッセージ追加のテスト"""
        sources = ['page 1', 'page 2']
        self.manager.add_message('assistant', '回答です', sources)
        messages = self.manager.load_history()

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['sources'], sources)

    def test_max_messages_limit(self):
        """最大メッセージ数制限のテスト"""
        # 15個のメッセージを追加（上限は10）
        for i in range(15):
            self.manager.add_message('user', f'メッセージ {i}')

        messages = self.manager.load_history()

        # 10個に制限されていることを確認
        self.assertEqual(len(messages), 10)

        # 最も新しい10個が保存されていることを確認
        self.assertEqual(messages[0]['content'], 'メッセージ 5')
        self.assertEqual(messages[-1]['content'], 'メッセージ 14')

    def test_clear_history(self):
        """履歴クリアのテスト"""
        self.manager.add_message('user', 'テスト')
        self.manager.add_message('assistant', '回答')

        self.manager.clear_history()
        messages = self.manager.load_history()

        self.assertEqual(len(messages), 0)

    def test_get_recent_messages(self):
        """最近のメッセージ取得のテスト"""
        for i in range(5):
            self.manager.add_message('user', f'メッセージ {i}')

        recent = self.manager.get_recent_messages(count=3)

        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0]['content'], 'メッセージ 2')

    def test_get_message_count(self):
        """メッセージ数取得のテスト"""
        self.assertEqual(self.manager.get_message_count(), 0)

        self.manager.add_message('user', 'テスト1')
        self.manager.add_message('user', 'テスト2')

        self.assertEqual(self.manager.get_message_count(), 2)


if __name__ == '__main__':
    unittest.main()
