import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Transaction:
    entry_id: str
    transaction_type: str
    amount: float
    label: str
    comments: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date_paid: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "label": self.label,
            "comments": self.comments,
            "id": self.id,
            "date_paid": self.date_paid.isoformat(),
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            entry_id=data.get("entry_id"),
            transaction_type=data.get("transaction_type"),
            amount=float(data["amount"]),
            label=data.get("label"),
            comments=data.get("comments"),
            id=data["id"],
            date_paid=datetime.fromisoformat(data["date_paid"]),
            tags=data.get("tags", []),
        )
    
class TransactionManager:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, entry_id: str, amount: float, transaction_type: str, label: str, comments: Optional[str] = None, tags: Optional[list[str]] = None) -> Transaction:
        new_transaction = Transaction(
            entry_id=entry_id,
            amount=amount,
            label=label,
            comments=comments,
            transaction_type=transaction_type,
            tags=tags if tags is not None else [],
        )
        self.transactions.append(new_transaction)
        return new_transaction
    
    def get_transactions_for_entry(self, entry_id: str) -> list[Transaction]:
        return [t for t in self.transactions if t.entry_id == entry_id]

    def get_all_transactions(self) -> list[Transaction]:
        return self.transactions
    
    def delete_transactions_by_entry_id(self, entry_id: str):
        """Deletes all transactions related to a parent entry."""
        self.transactions = [t for t in self.transactions if t.entry_id != entry_id]

    def delete_transaction_by_id(self, transaction_id: str):
        """Removes a single transaction by its own ID."""
        self.transactions = [t for t in self.transactions if t.id != transaction_id]