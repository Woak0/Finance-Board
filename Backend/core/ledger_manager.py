import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
import json

@dataclass
class LedgerEntry:
    label : str
    amount : float
    id : str = field(default_factory=lambda: str(uuid.uuid4()))
    date_incurred : datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    comments : Optional[str] = None
    status: str = "active"
    entry_type: str

    def to_dict(self):
        """ Converts the debt object into a dictionary to be printed into a JSON file which will be loaded later so the data saves to the program"""
        data = {
            "id" : self.id,
            "label" : self.label,
            "amount" : self.amount,
            "date_incurred" : self.date_incurred.isoformat(),
            "comments" : self.comments,
            "status" : self.status,
            "entry_type" : self.entry_type
        }
        return data
    
    @classmethod
    def from_dict(cls, data_dict):
        """ Used to create a debt object from the JSON file (complement of to_dict() function)"""
        label = data_dict["label"]

        amount_from_data_dict = data_dict["amount"]

        amount = float(amount_from_data_dict)

        id = data_dict["id"]

        date_incurred_str = data_dict["date_incurred"]
        date_incurred_obj = datetime.fromisoformat(date_incurred_str)

        comments = data_dict.get("comments")

        status = data_dict.get("status", "active")
        
        entry_type = data_dict.get("entry_type")

        return cls(
            label = label,
            amount = amount,
            id = id,
            date_incurred = date_incurred_obj,
            comments = comments,
            status = status,
            entry_type = entry_type
        )
    
class LedgerManager:
    def __init__(self):
        self.entries = []

    def add_entry(self, label: str, amount:float, entry_type: str, comments: Optional[str]=None, status: str = "active"):
        new_entry = LedgerEntry(label, amount, comments=comments, entry_type=entry_type)
        self.entries.append(new_entry)
        
        print(f"Entry '{new_entry.label}' added with ID {new_entry.id}")
        return new_entry
    
    def get_all_entries(self):
        return self.entries

    def get_entry_by_id(self, entry_id: str) -> Optional[LedgerEntry]:
        for entry_object in self.entries:
            if entry_object.id == entry_id:
                return entry_object
        return None
    
    def delete_entry_by_id(self, debt_id_to_delete: str):
        entries_to_keep = [entry for entry in self.entries if entry.id != debt_id_to_delete]
        self.entries = entries_to_keep
        return self.entries