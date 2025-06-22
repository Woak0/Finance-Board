from datetime import datetime, timedelta, timezone
from Backend.core.ledger_manager import LedgerEntry
from Backend.core.transaction_manager import Transaction
from Backend.core.summary_calculator import calculate_balance_for_entry

def suggest_snowball_priority(active_debts: list[LedgerEntry], all_transactions: list[Transaction]) -> LedgerEntry | None:
    """
    Analyzes active debts and suggests which to pay off first using the Snowball method.
    (Lowest balance first).
    """
    if not active_debts:
        return None
    
    debts_with_balance = []
    for debt in active_debts:
        balance = calculate_balance_for_entry(debt, all_transactions)
        if balance > 0:
            debts_with_balance.append((debt, balance))
            
    if not debts_with_balance:
        return None
        
    priority_debt, _ = min(debts_with_balance, key=lambda item: item[1])
    return priority_debt

def calculate_what_if_eta(all_entries, all_transactions, extra_monthly_payment: float) -> str:
    """
    Calculates a new 'debt-free' date based on a hypothetical extra monthly payment.
    This is a simplified simulation and does not use the complex velocity calculation.
    """
    debt_entries = [e for e in all_entries if e.entry_type == 'debt']
    if not debt_entries:
        return "No debts to calculate an ETA for."
        
    total_debt_balance = sum(calculate_balance_for_entry(d, all_transactions) for d in debt_entries)

    if total_debt_balance <= 0:
        return "All debts are already paid off!"

    if extra_monthly_payment <= 0:
        return "Extra payment must be positive to calculate a new ETA."

    months_to_go = total_debt_balance / extra_monthly_payment
    days_to_go = months_to_go * 30.44 # Average days in a month

    today = datetime.now(timezone.utc)
    freedom_date = today + timedelta(days=days_to_go)
    formatted_date = freedom_date.strftime("%b %d, %Y")
    
    return f"Hypothetical Debt-Free Date: {formatted_date}"