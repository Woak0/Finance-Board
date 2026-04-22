import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class LedgerEntry:
    label: str
    amount: float
    entry_type: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date_incurred: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    comments: Optional[str] = None
    status: str = "active"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "amount": self.amount,
            "date_incurred": self.date_incurred.isoformat(),
            "comments": self.comments,
            "status": self.status,
            "entry_type": self.entry_type,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            label=data["label"],
            amount=float(data["amount"]),
            id=data["id"],
            date_incurred=datetime.fromisoformat(data["date_incurred"]),
            comments=data.get("comments"),
            status=data.get("status", "active"),
            entry_type=data.get("entry_type"),
            tags=data.get("tags", []),
        )
    
class LedgerManager:
    def __init__(self):
        self.entries = []

    def add_entry(self, label: str, amount: float, entry_type: str, comments: Optional[str] = None, status: str = "active", tags: Optional[list[str]] = None):
        new_entry = LedgerEntry(
            label=label,
            amount=amount,
            entry_type=entry_type,
            comments=comments,
            status=status,
            tags=tags if tags is not None else [],
        )
        self.entries.append(new_entry)
        return new_entry
    
    def get_all_entries(self):
        return self.entries

    def get_entry_by_id(self, entry_id: str) -> Optional[LedgerEntry]:
        for entry_object in self.entries:
            if entry_object.id == entry_id:
                return entry_object
        return None
    
    def delete_entry_by_id(self, entry_id: str):
        self.entries = [e for e in self.entries if e.id != entry_id]