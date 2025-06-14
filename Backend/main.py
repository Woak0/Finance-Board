from typing import List, Optional
from Backend.core.ledger_manager import LedgerEntry, LedgerManager
from Backend.core.transaction_manager import Transaction, TransactionManager
from Backend.storage.storage_manager import StorageManager
from Backend.core.tag_manager import TagManager
from Backend.ui_helpers import *


def main():
    storage_manager = StorageManager()
    ledger_manager = LedgerManager()
    transaction_manager = TransactionManager()
    tag_manager = TagManager()

    all_data = storage_manager.load_data()
    list_of_entries_dicts = all_data["ledger_entries"]
    list_of_transactions_dicts = all_data["transactions"]

    hydrated_entries = [LedgerEntry.from_dict(entry_dict) for entry_dict in list_of_entries_dicts]
    hydrated_transactions = [Transaction.from_dict(trans_dict) for trans_dict in list_of_transactions_dicts]

    ledger_manager.entries = hydrated_entries
    transaction_manager.transactions = hydrated_transactions

    print("Welcome to your Financial Ledger!")
    print(f"Loaded {len(ledger_manager.entries)} entries and {len(transaction_manager.transactions)} transactions.")

    while True:
        print("\n--- Main Menu ---")
        print("[1] Add Debt | [2] Make Payment | [3] Add Loan | [4] Receive Repayment")
        print("[L] List All | [S] Summary | [E] Edit | [D] Delete | [X] Clear All")
        print("[Q] Quit and Save")

        choice = input("Enter your choice: ").lower()

        if choice == '1': handle_add_entry(ledger_manager, tag_manager, "debt")
        elif choice == '2': handle_add_transaction(ledger_manager, transaction_manager, "payment")
        elif choice == '3': handle_add_entry(ledger_manager, tag_manager, "loan")
        elif choice == '4': handle_add_transaction(ledger_manager, transaction_manager, "repayment")
        elif choice == 'l': handle_list_all(ledger_manager, transaction_manager)
        elif choice == 's': handle_show_summary(ledger_manager, transaction_manager)
        elif choice == 'e': handle_edit_entry_main(ledger_manager, transaction_manager, tag_manager)
        elif choice == 'd': handle_delete_entry(ledger_manager, transaction_manager)
        elif choice == 'x': handle_clear_all_data(ledger_manager, transaction_manager)
        elif choice == 'q': break
        else: print("Invalid choice.")

    print("\n--- Saving Data ---")
    storage_manager.save_data(ledger_manager=ledger_manager, transaction_manager=transaction_manager)
    print("Goodbye!")

if __name__ == "__main__":
    main()