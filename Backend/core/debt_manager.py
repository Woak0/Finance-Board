import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
import json

@dataclass
class Debt:
    label : str
    amount : float
    id : str = field(default_factory=lambda: str(uuid.uuid4()))
    date_incurred : datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    comments : Optional[str] = None
    status: str = "active"

    def to_dict(self):
        """ Converts the debt object into a dictionary to be printed into a JSON file which will be loaded later so the data saves to the program"""
        data = {
            "id" : self.id,
            "label" : self.label,
            "amount" : self.amount,
            "date_incurred" : self.date_incurred.isoformat(),
            "comments" : self.comments,
            "status" : self.status
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

        return cls(
            label = label,
            amount = amount,
            id = id,
            date_incurred = date_incurred_obj,
            comments = comments,
            status = status
        )
    
class DebtManager:
    def __init__(self):
        self.debts = []

    def add_debt(self, label: str, amount:float, comments: Optional[str]=None, status: str = "active"):
        new_debt = Debt(label, amount, comments=comments)
        self.debts.append(new_debt)
        
        print(f"Debt '{new_debt.label}' added with ID {new_debt.id}")
        return new_debt
    
    def get_all_debts(self):
        return self.debts

    def get_debt_by_id(self, debt_id: str) -> Optional[Debt]:
        for debt_object in self.debts:
            if debt_object.id == debt_id:
                return debt_object
        return None
    
    def delete_debt_by_id(self, debt_id_to_delete: str):
        kept_ids = [debt for debt in self.debts if debt.id != debt_id_to_delete]
        self.debts = kept_ids
        return self.debts


# --- Testing --- (Remove multi-line comment to test file)

"""
if __name__ == "__main__":
    # Test creating Debt objects
    debt_a1 = Debt(label="A1", amount=1305.48, comments="Initial amount from notebook")
    print("--- Debt A1 Object ---")
    print(debt_a1)

    print("\n--- Debt A1 as Dictionary (from to_dict) ---")
    debt_a1_dict = debt_a1.to_dict()
    print(debt_a1_dict)
    
    print("\n--- Debt A1 as JSON String ---")
    debt_a1_json_string = json.dumps(debt_a1_dict, indent=4) # indent makes it pretty
    print(debt_a1_json_string)

    print("\n--- Reconstructing Debt object from dictionary (debt_a1_dict) ---")
    reconstructed_debt_a1 = Debt.from_dict(debt_a1_dict)
    
    print(f"Reconstructed Object: {reconstructed_debt_a1}")
    print(f"Label: {reconstructed_debt_a1.label}, Type: {type(reconstructed_debt_a1.label)}")
    print(f"Amount: {reconstructed_debt_a1.amount}, Type: {type(reconstructed_debt_a1.amount)}")
    print(f"Date Incurred: {reconstructed_debt_a1.date_incurred}, Type: {type(reconstructed_debt_a1.date_incurred)}") # Should be <class 'datetime.datetime'>
    print(f"ID: {reconstructed_debt_a1.id}, Type: {type(reconstructed_debt_a1.id)}")
    print(f"Comments: {reconstructed_debt_a1.comments}, Type: {type(reconstructed_debt_a1.comments)}")

    # Test with missing optional fields
    sample_dict_missing_optional = {
        "id": str(uuid.uuid4()), 
        "label": "Test Debt Min",
        "amount": 100.00,
        "date_incurred": datetime.now(timezone.utc).isoformat() 
    }
    print("\n--- Reconstructing Debt object from dictionary with missing optional fields ---")
    debt_from_min_dict = Debt.from_dict(sample_dict_missing_optional)
    print(f"Reconstructed Minimal Debt: {debt_from_min_dict}")
    print(f"Comments (should be None): {debt_from_min_dict.comments}")
    print(f"Expected Repayment (should be None): {debt_from_min_dict.expected_repayment_timeframe}")

    # Test creating an object using only mandatory fields, letting defaults apply
    print("\n--- Debt object with only mandatory fields (defaults apply) ---")
    debt_minimal_args = Debt(label="Minimal Args Debt", amount=50.25)
    print(debt_minimal_args)
    print(f"ID (auto-generated): {debt_minimal_args.id}")
    print(f"Date Incurred (auto-generated): {debt_minimal_args.date_incurred}")
    print(f"Comments (default): {debt_minimal_args.comments}")

    print("\n--- Testing DebtManager ---")
    manager = DebtManager()

    print("\nAdding debts...")
    debt1 = manager.add_debt(label="Groceries", amount=70.00, comments="Weekly Shopping")
    debt2 = manager.add_debt(label="Concert Tickets", amount=120.00)
    debt3 = manager.add_debt(label="Books", amount=35.20, expected_repayment_timeframe="1 month")

    print("\nAll debts in manager:")
    all_my_debts = manager.get_all_debts()
    if not all_my_debts:
        print("No debts in the manager.")
    else:
        for d in all_my_debts:
            print(f"  - ID: {d.id}, Label: {d.label}, Amount: {d.amount}")

    print(f"\nSearching for debt with ID: {debt1.id}")
    found_debt = manager.get_debt_by_id(debt1.id)
    if found_debt:
        print(f"Found: Label: {found_debt.label}, Amount: {found_debt.amount}")
    else:
        print(f"Debt with ID {debt1.id} not found.")


    fake_id = "this-id-does-not-exist"
    print(f"\nSearching for debt with ID: {fake_id}")
    not_found_debt = manager.get_debt_by_id(fake_id)
    if not_found_debt:
        print(f"Found: Label: {not_found_debt.label}, Amount: {not_found_debt.amount}")
    else:
        print(f"Debt with ID {fake_id} not found (Correctly returned None).")
"""
