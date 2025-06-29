from Backend.core.ledger_manager import LedgerManager
from Backend.core.transaction_manager import TransactionManager

def populate_with_test_data(ledger_mngr: LedgerManager, trans_mngr: TransactionManager):
    """
    Populates the managers with some default data for development and testing.
    This function should only be called if the data files are empty.
    """
    print("--- No existing data found. Populating with test data. ---")

    # --- Create some Ledger Entries ---
    
    # A debt with a couple of payments
    car_loan = ledger_mngr.add_entry(
        label="Car Loan",
        amount=15000.00,
        entry_type="debt",
        tags=["Vehicle & Transport", "Loan"]
    )

    # A maxed-out credit card
    credit_card = ledger_mngr.add_entry(
        label="Visa Credit Card",
        amount=2500.00,
        entry_type="debt",
        tags=["Credit Card", "Fees & Interest"]
    )
    
    # A personal loan to a friend
    friend_loan = ledger_mngr.add_entry(
        label="Loan to Sarah",
        amount=300.00,
        entry_type="loan",
        tags=["Personal", "Loan"]
    )

    # A paid-off debt, for testing filters later
    paid_debt = ledger_mngr.add_entry(
        label="Old Phone Bill",
        amount=120.00,
        entry_type="debt",
        status="paid", # Manually setting status for this test case
        tags=["Utilities"]
    )

    # --- Add some Transactions ---
    
    # Two payments on the car loan
    if car_loan:
        trans_mngr.add_transaction(
            entry_id=car_loan.id,
            amount=450.00,
            transaction_type="payment",
            label="Car Payment - Jan"
        )
        trans_mngr.add_transaction(
            entry_id=car_loan.id,
            amount=450.00,
            transaction_type="payment",
            label="Car Payment - Feb"
        )
    
    # A repayment from the friend
    if friend_loan:
        trans_mngr.add_transaction(
            entry_id=friend_loan.id,
            amount=50.00,
            transaction_type="repayment",
            label="Sarah paid back some"
        )