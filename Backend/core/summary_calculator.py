from typing import List
from datetime import datetime, timedelta, timezone
from Backend.core.debt_manager import Debt
from Backend.core.payment_manager import Payment

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

def calculate_remaining_balance_for_specific_debt(debt_object: Debt, all_payments: list[Payment]) -> float:
    initial_debt_amount = debt_object.amount

    total_paid_for_this_debt = calculate_payments_for_specific_debt(debt_id = debt_object.id, all_payments=all_payments)

    remaining_balance = initial_debt_amount - total_paid_for_this_debt

    return remaining_balance

def get_payments_for_debt(debt_id: str, all_payments: list[Payment]) -> list[Payment]:
    payments_for_this_debt = []

    for payments in all_payments:
        if payments.debt_id == debt_id:
            payments_for_this_debt.append(payments)

    return payments_for_this_debt

def calculate_smart_eta(debt: Debt, all_payments: list[Payment]) -> str:
    payments_for_this_debt = get_payments_for_debt(debt.id, all_payments)

    num_payments = len(payments_for_this_debt)

    if num_payments == 0:
        return "N/A (No payments yet)."
    elif num_payments == 1:
        one_payment = payments_for_this_debt[0]

        if one_payment.amount <= 0:
            return "N/A"
        eta = debt.amount / one_payment.amount
        return f"Approx. {round(eta)} payments"
    else:
        payments_for_this_debt.sort(key=lambda p: p.date_paid)

        total_paid = sum(p.amount for p in payments_for_this_debt)

        remaining_balance = debt.amount - total_paid
        if remaining_balance <= 0:
            return "Paid"
        
        earliest_date = payments_for_this_debt[0].date_paid
        latest_date = payments_for_this_debt[-1].date_paid

        duration = latest_date - earliest_date
        duration_in_days = duration.days

        if duration_in_days < 1:
            duration_in_days = 1
        
        velocity = total_paid / duration_in_days

        if velocity <= 0:
            return "N/A"
        
        days_to_go = remaining_balance / velocity

        today = datetime.now(timezone.utc)

        eta_date = today + timedelta(days=days_to_go)

        formatted_date = eta_date.strftime("%b %d, %Y")

        return f"ETA: {formatted_date}"
        



