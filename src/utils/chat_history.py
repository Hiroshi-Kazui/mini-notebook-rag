import json
import os
from typing import List, Dict
from datetime import datetime
from pathlib import Path


class ChatHistoryManager:
    """
    チャット履歴を管理するクラス（上限50メッセージ）
    """
    def __init__(self, history_file: str = "storage/chat_history.json", max_messages: int = 50):
        """
        Args:
            history_file: 履歴ファイルのパス
            max_messages: 保存する最大メッセージ数（デフォルト: 50）
        """
        self.history_file = Path(history_file)
        self.max_messages = max_messages
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """履歴ファイルのディレクトリとファイルを作成"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            self._save_history([])

    def _save_history(self, messages: List[Dict]):
        """履歴をファイルに保存"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def load_history(self) -> List[Dict]:
        """
        履歴をロード

        Returns:
            メッセージのリスト
        """
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def add_message(self, role: str, content: str, sources: List[str] = None):
        """
        メッセージを追加（上限を超えた場合は古いものを削除）

        Args:
            role: メッセージの役割 ('user' または 'assistant')
            content: メッセージ内容
            sources: ソース情報（オプション）
        """
        messages = self.load_history()

        # 新しいメッセージを追加
        new_message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        if sources:
            new_message['sources'] = sources

        messages.append(new_message)

        # 上限を超えた場合、古いメッセージを削除
        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages:]

        self._save_history(messages)

    def clear_history(self):
        """履歴をクリア"""
        self._save_history([])

    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """
        最近のメッセージを取得

        Args:
            count: 取得するメッセージ数

        Returns:
            最近のメッセージのリスト
        """
        messages = self.load_history()
        return messages[-count:] if messages else []

    def get_message_count(self) -> int:
        """
        保存されているメッセージ数を取得

        Returns:
            メッセージ数
        """
        return len(self.load_history())

    def export_history(self, export_path: str):
        """
        履歴を別のファイルにエクスポート

        Args:
            export_path: エクスポート先のパス
        """
        messages = self.load_history()
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
