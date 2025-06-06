from typing import List
from debt_manager import Debt
from payment_manager import Payment

def calculate_total_debt_incurred(debts: list[Debt]) -> float:
    total_debt_incurred = 0.0

    for debt_object in debts:
        total_debt_incurred = total_debt_incurred + debt_object.amount
    
    return total_debt_incurred

def calculate_total_amount_paid(payments: list[Payment]) -> float:
    total_amount_paid = 0.0

    for payment_object in payments:
        total_amount_paid = total_amount_paid + payment_object.amount

    return total_amount_paid

def calculate_overall_remaining_balance(total_debt_incurred: float, total_amount_paid: float) -> float:
    return total_debt_incurred - total_amount_paid

def calculate_payments_for_specific_debt(debt_id: str, all_payments: list[Payment]) -> float:
    total_paid_for_this_debt = 0.0

    for payment_object in all_payments:
        if payment_object.debt_id == debt_id:
            total_paid_for_this_debt = total_paid_for_this_debt + payment_object.amount
    return total_paid_for_this_debt




            