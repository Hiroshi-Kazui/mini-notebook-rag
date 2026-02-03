import json
from typing import List, Dict
from datetime import datetime
from pathlib import Path

from src.config import settings


class ChatHistoryManager:
    """Manage chat history per notebook."""

    def __init__(self, notebook_id: str = "default", history_dir: str = None, max_messages: int = 50):
        self.notebook_id = notebook_id
        self.history_dir = Path(history_dir or settings.storage.chat_history_dir)
        self.history_file = self.history_dir / f"{notebook_id}.json"
        self.max_messages = max_messages
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        self.history_dir.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            self._save_history([])

    def _save_history(self, messages: List[Dict]):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def load_history(self) -> List[Dict]:
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def add_message(self, role: str, content: str, sources: List[str] = None):
        messages = self.load_history()

        new_message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if sources:
            new_message["sources"] = sources

        messages.append(new_message)

        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages :]

        self._save_history(messages)

    def clear_history(self):
        self._save_history([])

    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        messages = self.load_history()
        return messages[-count:] if messages else []

    def get_message_count(self) -> int:
        return len(self.load_history())

    def export_history(self, export_path: str):
        messages = self.load_history()
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)

    def switch_notebook(self, new_notebook_id: str):
        self.notebook_id = new_notebook_id
        self.history_file = self.history_dir / f"{new_notebook_id}.json"
        self._ensure_file_exists()

