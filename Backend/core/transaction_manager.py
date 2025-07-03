import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
import json

@dataclass
class Transaction:
    entry_id : str
    transaction_type : str
    amount : float
    label : str
    comments : Optional[str] = None
    id : str = field(default_factory=lambda: str(uuid.uuid4()))
    date_paid : datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags : list[str] = field(default_factory=list)
    

    def to_dict(self):
        data = {
            "entry_id" : self.entry_id,
            "transaction_type" : self.transaction_type,
            "amount" : self.amount,
            "label" : self.label,
            "comments" : self.comments,
            "id" : self.id,
            "date_paid" : self.date_paid.isoformat(),
            "tags" : self.tags
        }
        return data
    

    @classmethod
    def from_dict(cls, data_dict):
        entry_id = data_dict.get("entry_id")

        amount_from_data_dict = data_dict["amount"]
        amount = float(amount_from_data_dict)

        label = data_dict.get("label")
        comments = data_dict.get("comments")

        id = data_dict["id"]

        date_paid_from_dict = data_dict["date_paid"]
        date_paid = datetime.fromisoformat(date_paid_from_dict)

        transaction_type = data_dict.get("transaction_type")

        tags = data_dict.get("tags", [])

        return cls(
            entry_id = entry_id,
            amount = amount,
            label = label,
            comments = comments,
            id = id,
            date_paid = date_paid,
            transaction_type = transaction_type,
            tags = tags
        )
    
class TransactionManager:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, entry_id : str, amount : float, transaction_type: str, label : str, comments : Optional[str] = None, tags: Optional[list[str]] = None) -> Transaction:
        tags_to_save = tags if tags is not None else []

        new_transaction = Transaction(
            entry_id = entry_id, 
            amount = amount, 
            label=label, 
            comments=comments, 
            transaction_type=transaction_type, 
            tags = tags_to_save
            )
        
        self.transactions.append(new_transaction)

        print(f"Transaction of ${new_transaction.amount} has been made for entry {new_transaction.entry_id} (ID: {new_transaction.id})")

        return new_transaction
    
    def get_transactions_for_entry(self, entry_id: str) -> list[Transaction]:
        TransactionList = []

        for transaction_object in self.transactions:
            if transaction_object.entry_id == entry_id:
                TransactionList.append(transaction_object)

        return TransactionList

    def get_all_transactions(self) -> list[Transaction]:
        return self.transactions
    
    def delete_transactions_by_entry_id(self, transaction_id_to_delete: str):
        """
        Deletes all transactions related to a parent entry.
        """
        transactions_to_keep = [transaction for transaction in self.transactions if transaction.entry_id != transaction_id_to_delete]
        self.transactions = transactions_to_keep
        return self.transactions
    
    def delete_transaction_by_id(self, transaction_id_to_delete: str):
        """Removes a single transaction from the list by its own ID."""
        
        initial_count = len(self.transactions)
        self.transactions = [t for t in self.transactions if t.id != transaction_id_to_delete]
        if len(self.transactions) < initial_count:
            print(f"Deleted transaction with ID: {transaction_id_to_delete}")