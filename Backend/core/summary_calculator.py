from typing import List
from datetime import datetime, timedelta, timezone
from Backend.core.ledger_manager import LedgerEntry
from Backend.core.transaction_manager import Transaction

def calculate_total_entry_amount(entries: list[LedgerEntry]) -> float:
    """Calculates the sum of amounts for a list of ledger entries."""
    total_amount = 0.0
    for entry in entries:
        total_amount += entry.amount
    return total_amount

def calculate_total_transaction_amount(transactions: list[Transaction]) -> float:
    """Calculates the sum of amounts for a list of transactions."""
    total_amount = 0.0
    for transaction in transactions:
        total_amount += transaction.amount
    return total_amount

def calculate_overall_balance(total_entries: float, total_transactions: float) -> float:
    """Calculates the overall remaining balance."""
    return total_entries - total_transactions

def get_transactions_for_entry(entry_id: str, all_transactions: list[Transaction]) -> list[Transaction]:
    """Returns a list of all transactions associated with a specific ledger entry."""
    transactions_for_this_entry = []
    for transaction in all_transactions:
        if transaction.entry_id == entry_id:
            transactions_for_this_entry.append(transaction)
    return transactions_for_this_entry

def calculate_balance_for_entry(entry: LedgerEntry, all_transactions: list[Transaction]) -> float:
    """Calculates the remaining balance for a single ledger entry."""
    transactions_for_this_entry = get_transactions_for_entry(entry.id, all_transactions)
    total_paid_for_this_entry = calculate_total_transaction_amount(transactions_for_this_entry)
    remaining_balance = entry.amount - total_paid_for_this_entry
    return remaining_balance

def calculate_entry_eta(entry: LedgerEntry, all_transactions: list[Transaction]) -> str:
    """Calculates the smart ETA for a single ledger entry."""
    transactions_for_this_entry = get_transactions_for_entry(entry.id, all_transactions)
    num_transactions = len(transactions_for_this_entry)

    if num_transactions == 0:
        return "N/A (No transactions yet)"
    
    current_balance = calculate_balance_for_entry(entry, all_transactions)
    if current_balance <= 0:
        return "Paid Off"

    if num_transactions == 1:
        the_one_transaction = transactions_for_this_entry[0]
        if the_one_transaction.amount <= 0:
            return "N/A"
        eta_in_payments = entry.amount / the_one_transaction.amount
        return f"Approx. {round(eta_in_payments)} more transactions"
    
    transactions_for_this_entry.sort(key=lambda t: t.date_paid)
    earliest_date = transactions_for_this_entry[0].date_paid
    latest_date = transactions_for_this_entry[-1].date_paid
    
    duration = latest_date - earliest_date
    duration_in_days = duration.days
    if duration_in_days < 1:
        duration_in_days = 1

    total_paid = calculate_total_transaction_amount(transactions_for_this_entry)
    velocity = total_paid / duration_in_days
    if velocity <= 0:
        return "N/A"
        
    days_to_go = current_balance / velocity
    today = datetime.now(timezone.utc)
    eta_date = today + timedelta(days=days_to_go)
    formatted_date = eta_date.strftime("%b %d, %Y")
    return f"ETA: {formatted_date}"
    
def calculate_overall_eta(all_entries: list[LedgerEntry], all_transactions: list[Transaction]) -> str:
    """Calculates the overall estimated payoff date for all active debts."""
    
    num_transactions = len(all_transactions)
    if num_transactions < 1:
        return "N/A (No transactions yet)"

    debt_entries = [e for e in all_entries if e.entry_type == 'debt']
    
    total_debt = calculate_total_entry_amount(debt_entries)
    total_paid = calculate_total_transaction_amount(all_transactions) 
    remaining_balance = total_debt - total_paid

    if remaining_balance <= 0:
        return "All debts are paid off!"

    active_debts = [d for d in debt_entries if d.status == 'active']
    if not active_debts:
        return "All debts are paid off!"

    start_date = min(active_debts, key=lambda d: d.date_incurred).date_incurred
    latest_payment_date = max(all_transactions, key=lambda p: p.date_paid).date_paid
    duration = latest_payment_date - start_date
    duration_in_days = duration.days

    if duration_in_days < 1:
        return "N/A (More time needed for a prediction)"

    overall_velocity = total_paid / duration_in_days
    if overall_velocity <= 0:
        return "N/A (Payment velocity not positive)"

    days_to_go = remaining_balance / overall_velocity
    if days_to_go > 73000:
        return "Debt-Free By: Over 200 years"
    
    today = datetime.now(timezone.utc)
    freedom_date = today + timedelta(days=days_to_go)
    formatted_date = freedom_date.strftime("%b %d, %Y")
    return f"Debt-Free By: {formatted_date}"