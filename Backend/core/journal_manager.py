import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class JournalEntry:
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "date_created": self.date_created.isoformat(),
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            content=data["content"],
            id=data["id"],
            date_created=datetime.fromisoformat(data["date_created"]),
            tags=data.get("tags", []),
        )

class JournalManager:
    def __init__(self):
        self.entries: list[JournalEntry] = []

    def add_entry(self, content: str, tags: Optional[list[str]] = None):
        new_entry = JournalEntry(content=content, tags=tags if tags is not None else [])
        self.entries.append(new_entry)
        return new_entry

    def get_all_entries(self) -> list[JournalEntry]:
        return sorted(self.entries, key=lambda e: e.date_created, reverse=True)

    def delete_entry_by_id(self, entry_id: str):
        self.entries = [e for e in self.entries if e.id != entry_id]