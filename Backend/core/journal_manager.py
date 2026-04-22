import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_NOTEBOOK = "General"

@dataclass
class JournalEntry:
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = field(default_factory=list)
    notebook: str = DEFAULT_NOTEBOOK

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "date_created": self.date_created.isoformat(),
            "tags": self.tags,
            "notebook": self.notebook,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            content=data["content"],
            id=data["id"],
            date_created=datetime.fromisoformat(data["date_created"]),
            tags=data.get("tags", []),
            notebook=data.get("notebook", DEFAULT_NOTEBOOK),
        )

class JournalManager:
    def __init__(self):
        self.entries: list[JournalEntry] = []

    def add_entry(self, content: str, notebook: str = DEFAULT_NOTEBOOK, tags: Optional[list[str]] = None):
        new_entry = JournalEntry(content=content, notebook=notebook, tags=tags if tags is not None else [])
        self.entries.append(new_entry)
        return new_entry

    def get_all_entries(self) -> list[JournalEntry]:
        return sorted(self.entries, key=lambda e: e.date_created, reverse=True)

    def get_entries_by_notebook(self, notebook: str) -> list[JournalEntry]:
        return sorted(
            [e for e in self.entries if e.notebook == notebook],
            key=lambda e: e.date_created, reverse=True,
        )

    def get_notebooks(self) -> list[str]:
        """Returns a sorted list of unique notebook names."""
        notebooks = sorted(set(e.notebook for e in self.entries))
        # Always put "General" first if it exists
        if DEFAULT_NOTEBOOK in notebooks:
            notebooks.remove(DEFAULT_NOTEBOOK)
            notebooks.insert(0, DEFAULT_NOTEBOOK)
        return notebooks

    def delete_entry_by_id(self, entry_id: str):
        self.entries = [e for e in self.entries if e.id != entry_id]
