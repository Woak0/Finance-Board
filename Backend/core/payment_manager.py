import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
import json

@dataclass
class Payment:
    debt_id : str
    amount : float
    label : Optional[str] = None
    comments : Optional[str] = None
    id : str = field(default_factory=lambda: str(uuid.uuid4()))
    date_paid : datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        data = {
            "debt_id" : self.debt_id,
            "amount" : self.amount,
            "label" : self.label,
            "comments" : self.comments,
            "id" : self.id,
            "date_paid" : self.date_paid.isoformat()
        }
        return data
    

    @classmethod
    def from_dict(cls, data_dict):
        debt_id = data_dict["debt_id"]

        amount_from_data_dict = data_dict["amount"]
        amount = float(amount_from_data_dict)

        label = data_dict.get("label")
        comments = data_dict.get("comments")

        id = data_dict["id"]

        date_paid_from_dict = data_dict["date_paid"]
        date_paid = datetime.fromisoformat(date_paid_from_dict)

        return cls(
            debt_id = debt_id,
            amount = amount,
            label = label,
            comments = comments,
            id = id,
            date_paid = date_paid
        )
    
class PaymentManager:
    def __init__(self):
        self.payments = []

    def add_payment(self, debt_id : str, amount : float, label : Optional[str] = None, comments : Optional[str] = None) -> Payment:
        new_payment = Payment(debt_id = debt_id, amount = amount, label=label, comments=comments)
        self.payments.append(new_payment)

        print(f"Payment of {new_payment.amount} has been made for debt {new_payment.debt_id} (ID: {new_payment.id})")

        return new_payment
    
    def get_payments_for_debt(self, debt_id: str) -> list[Payment]:
        Paylist = []

        for payment_object in self.payments:
            if payment_object.debt_id == debt_id:
                Paylist.append(payment_object)

        return Paylist


    def get_all_payments(self) -> list[Payment]:
        return self.payments


# --- Testing --- (Remove multi-line comment to test file)
"""
if __name__ == "__main__":
    print("--- Testing Payment Class ---")

    # For testing, we need a placeholder debt_id
    sample_debt_id = str(uuid.uuid4())
    print(f"Using sample_debt_id for tests: {sample_debt_id}")

    # 1. Create a Payment object with all fields
    print("\n1. Creating full Payment object:")
    payment1 = Payment(
        debt_id=sample_debt_id,
        amount=50.75,
        label="P1",
        comments="First partial payment"
    )
    print(payment1)
    print(f"  - Payment ID (auto): {payment1.id}")
    print(f"  - Date Paid (auto): {payment1.date_paid}")

    # 2. Convert Payment object to dictionary
    print("\n2. Payment object to_dict():")
    payment1_dict = payment1.to_dict()
    print(json.dumps(payment1_dict, indent=4)) # Pretty print JSON
    assert payment1_dict["debt_id"] == sample_debt_id
    assert payment1_dict["amount"] == 50.75
    assert isinstance(payment1_dict["date_paid"], str) # Ensure date is string

    # 3. Reconstruct Payment object from dictionary
    print("\n3. Reconstructing Payment from_dict():")
    reconstructed_payment1 = Payment.from_dict(payment1_dict)
    print(reconstructed_payment1)
    assert reconstructed_payment1.id == payment1.id
    assert reconstructed_payment1.debt_id == payment1.debt_id
    assert reconstructed_payment1.amount == payment1.amount
    assert isinstance(reconstructed_payment1.date_paid, datetime) # Ensure date is datetime object
    assert reconstructed_payment1.label == "P1"
    assert reconstructed_payment1.comments == "First partial payment"
    print(f"  - Reconstructed Date Paid Type: {type(reconstructed_payment1.date_paid)}")


    # 4. Create a Payment object with only mandatory fields
    print("\n4. Creating Payment object with only mandatory fields:")
    payment2 = Payment(
        debt_id=sample_debt_id,
        amount=100.00
    )
    print(payment2)
    assert payment2.label is None
    assert payment2.comments is None
    print(f"  - Payment ID (auto): {payment2.id}")
    print(f"  - Date Paid (auto): {payment2.date_paid}")

    payment2_dict = payment2.to_dict()
    print("  - to_dict() output for minimal payment:")
    print(json.dumps(payment2_dict, indent=4))


    # 5. Test from_dict with a dictionary missing optional fields
    print("\n5. Test from_dict() with dictionary missing optional fields:")
    minimal_payment_dict = {
        "id": str(uuid.uuid4()),
        "debt_id": sample_debt_id,
        "amount": 25.00,
        "date_paid": datetime.now(timezone.utc).isoformat()
        # 'label' and 'comments' are deliberately missing
    }
    reconstructed_minimal_payment = Payment.from_dict(minimal_payment_dict)
    print(reconstructed_minimal_payment)
    assert reconstructed_minimal_payment.label is None, f"Label should be None, but got {reconstructed_minimal_payment.label}"
    assert reconstructed_minimal_payment.comments is None, f"Comments should be None, but got {reconstructed_minimal_payment.comments}"
    print("  - Successfully reconstructed with missing optional fields (label/comments are None).")

    print("\n--- Payment Class Testing Complete ---")
"""