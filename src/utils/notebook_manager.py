import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from src.config import settings


class NotebookManager:
    """Manage notebook metadata, sources, and current notebook selection."""

    def __init__(self, metadata_file: str = None):
        self.metadata_file = Path(
            metadata_file or settings.storage.notebook_metadata_file
        )
        self.max_notebooks = settings.app.max_notebooks_per_user
        self.default_notebook_name = settings.app.default_notebook_name
        self._ensure_metadata_file()

    def _now(self) -> str:
        return datetime.now().isoformat()

    def _default_metadata(self) -> Dict:
        return {
            "notebooks": {},
            "sources": {},
            "current_notebook": "default",
        }

    def _ensure_metadata_file(self) -> None:
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.metadata_file.exists():
            data = self._default_metadata()
            data["notebooks"]["default"] = {
                "id": "default",
                "name": self.default_notebook_name,
                "created_at": self._now(),
                "updated_at": self._now(),
                "description": "Default notebook",
                "source_count": 0,
            }
            data["sources"]["default"] = []
            self._save_metadata(data)
        else:
            data = self._load_metadata()
            changed = False
            for key, value in self._default_metadata().items():
                if key not in data:
                    data[key] = value
                    changed = True
            if "default" not in data.get("notebooks", {}):
                data.setdefault("notebooks", {})
                data["notebooks"]["default"] = {
                    "id": "default",
                    "name": self.default_notebook_name,
                    "created_at": self._now(),
                    "updated_at": self._now(),
                    "description": "Default notebook",
                    "source_count": 0,
                }
                data.setdefault("sources", {})
                data["sources"].setdefault("default", [])
                data["current_notebook"] = "default"
                changed = True
            if changed:
                self._save_metadata(data)

    def _load_metadata(self) -> Dict:
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._default_metadata()

    def _save_metadata(self, data: Dict) -> None:
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_notebook_id(self) -> str:
        return f"notebook_{uuid.uuid4().hex[:8]}"

    def validate_notebook_name(self, name: str) -> Tuple[bool, str]:
        if not name or not name.strip():
            return False, "Notebook name is required."
        for nb in self.list_notebooks():
            if nb["name"].lower() == name.strip().lower():
                return False, "Notebook name already exists."
        return True, ""

    def create_notebook(self, name: str, description: str = "") -> Dict:
        data = self._load_metadata()
        if len(data.get("notebooks", {})) >= self.max_notebooks:
            return {
                "success": False,
                "message": f"Maximum notebooks reached ({self.max_notebooks}).",
            }
        ok, msg = self.validate_notebook_name(name)
        if not ok:
            return {"success": False, "message": msg}

        notebook_id = self._generate_notebook_id()
        data.setdefault("notebooks", {})
        data.setdefault("sources", {})
        data["notebooks"][notebook_id] = {
            "id": notebook_id,
            "name": name.strip(),
            "created_at": self._now(),
            "updated_at": self._now(),
            "description": description.strip(),
            "source_count": 0,
        }
        data["sources"][notebook_id] = []
        self._save_metadata(data)
        return {"success": True, "message": "Notebook created.", "id": notebook_id}

    def get_notebook(self, notebook_id: str) -> Dict:
        data = self._load_metadata()
        return data.get("notebooks", {}).get(notebook_id, {})

    def list_notebooks(self) -> List[Dict]:
        data = self._load_metadata()
        notebooks = list(data.get("notebooks", {}).values())
        return sorted(
            notebooks,
            key=lambda n: n.get("updated_at", ""),
            reverse=True,
        )

    def update_notebook(self, notebook_id: str, name: str = None, description: str = None) -> Dict:
        data = self._load_metadata()
        notebook = data.get("notebooks", {}).get(notebook_id)
        if not notebook:
            return {"success": False, "message": "Notebook not found."}

        if name is not None:
            ok, msg = self.validate_notebook_name(name)
            if not ok and name.strip().lower() != notebook["name"].lower():
                return {"success": False, "message": msg}
            notebook["name"] = name.strip()
        if description is not None:
            notebook["description"] = description.strip()

        notebook["updated_at"] = self._now()
        data["notebooks"][notebook_id] = notebook
        self._save_metadata(data)
        return {"success": True, "message": "Notebook updated."}

    def delete_notebook(self, notebook_id: str, delete_sources: bool = True) -> Dict:
        data = self._load_metadata()
        if notebook_id == data.get("current_notebook"):
            return {
                "success": False,
                "message": "Cannot delete the current notebook.",
            }
        if notebook_id not in data.get("notebooks", {}):
            return {"success": False, "message": "Notebook not found."}

        if delete_sources:
            data.get("sources", {}).pop(notebook_id, None)
        data.get("notebooks", {}).pop(notebook_id, None)
        self._save_metadata(data)
        return {"success": True, "message": "Notebook deleted."}

    def get_current_notebook(self) -> str:
        data = self._load_metadata()
        return data.get("current_notebook", "default")

    def set_current_notebook(self, notebook_id: str) -> bool:
        data = self._load_metadata()
        if notebook_id not in data.get("notebooks", {}):
            return False
        data["current_notebook"] = notebook_id
        self._save_metadata(data)
        return True

    def add_source(self, notebook_id: str, filename: str, chunk_count: int, file_size_mb: float) -> bool:
        data = self._load_metadata()
        if notebook_id not in data.get("notebooks", {}):
            return False
        sources = data.get("sources", {}).setdefault(notebook_id, [])
        if any(s["filename"] == filename for s in sources):
            return True
        sources.append(
            {
                "filename": filename,
                "added_at": self._now(),
                "chunk_count": chunk_count,
                "file_size_mb": round(file_size_mb, 2),
            }
        )
        data["notebooks"][notebook_id]["source_count"] = len(sources)
        data["notebooks"][notebook_id]["updated_at"] = self._now()
        self._save_metadata(data)
        return True

    def list_sources(self, notebook_id: str) -> List[Dict]:
        data = self._load_metadata()
        return data.get("sources", {}).get(notebook_id, [])

    def remove_source(self, notebook_id: str, filename: str) -> bool:
        data = self._load_metadata()
        sources = data.get("sources", {}).get(notebook_id, [])
        new_sources = [s for s in sources if s["filename"] != filename]
        if len(new_sources) == len(sources):
            return False
        data["sources"][notebook_id] = new_sources
        data["notebooks"][notebook_id]["source_count"] = len(new_sources)
        data["notebooks"][notebook_id]["updated_at"] = self._now()
        self._save_metadata(data)
        return True

    def get_notebook_stats(self, notebook_id: str) -> Dict:
        notebook = self.get_notebook(notebook_id)
        source_count = notebook.get("source_count", 0)
        message_count = 0
        try:
            from src.utils.chat_history import ChatHistoryManager

            chat_mgr = ChatHistoryManager(notebook_id=notebook_id)
            message_count = chat_mgr.get_message_count()
        except Exception:
            message_count = 0
        return {
            "source_count": source_count,
            "message_count": message_count,
        }

    def needs_migration(self) -> bool:
        data = self._load_metadata()
        old_history = Path(settings.storage.chat_history_path)
        raw_dir = Path(settings.storage.data_raw_dir)
        has_old = old_history.exists() or any(raw_dir.glob("*.pdf"))
        if not has_old:
            return False
        default_sources = data.get("sources", {}).get("default", [])
        return len(default_sources) == 0

    def migrate_existing_data(self) -> Dict:
        data = self._load_metadata()
        if "default" not in data.get("notebooks", {}):
            data.setdefault("notebooks", {})
            data["notebooks"]["default"] = {
                "id": "default",
                "name": self.default_notebook_name,
                "created_at": self._now(),
                "updated_at": self._now(),
                "description": "Default notebook",
                "source_count": 0,
            }
        data.setdefault("sources", {})
        data["sources"].setdefault("default", [])
        data["current_notebook"] = data.get("current_notebook", "default")
        self._save_metadata(data)

        raw_dir = Path(settings.storage.data_raw_dir)
        processed_dir = Path(settings.storage.data_processed_dir)
        for pdf_file in raw_dir.glob("*.pdf"):
            processed_file = processed_dir / f"{pdf_file.stem}.json"
            if processed_file.exists():
                try:
                    with open(processed_file, "r", encoding="utf-8") as f:
                        chunks = json.load(f)
                    chunk_count = len(chunks)
                except Exception:
                    chunk_count = 0
            else:
                chunk_count = 0
            file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
            self.add_source("default", pdf_file.name, chunk_count, file_size_mb)

        try:
            from src.embedding.store import add_notebook_id_to_existing_chunks

            add_notebook_id_to_existing_chunks("default")
        except Exception:
            pass

        old_history = Path(settings.storage.chat_history_path)
        if old_history.exists():
            new_dir = Path(settings.storage.chat_history_dir)
            new_dir.mkdir(parents=True, exist_ok=True)
            new_history = new_dir / "default.json"
            try:
                if not new_history.exists():
                    new_history.write_text(
                        old_history.read_text(encoding="utf-8"), encoding="utf-8"
                    )
                backup_path = old_history.with_suffix(".json.backup")
                old_history.rename(backup_path)
            except Exception:
                pass

        return {"success": True, "message": "Migration completed."}

