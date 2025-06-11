from typing import List, Optional
from Backend.core.ledger_manager import LedgerEntry, LedgerManager
from Backend.core.transaction_manager import Transaction, TransactionManager
from Backend.storage.storage_manager import StorageManager
from Backend.core.summary_calculator import (
    calculate_total_entry_amount,
    calculate_total_transaction_amount,
    calculate_overall_balance,
    calculate_balance_for_entry,
    get_transactions_for_entry,
    calculate_entry_eta,
    calculate_overall_eta,
)

def main():
    storage_manager = StorageManager()
    ledger_manager = LedgerManager()
    transaction_manager = TransactionManager()

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
        print("[1] Add a new Debt") 
        print("[2] Make a Payment on a Debt")
        print("[3] Add a new Loan")
        print("[4] Receive a Repayment for a loan")
        print("[L] List all Entries & Transactions")
        print("[E] Edit an entry (Debt or Loan)")
        print("[S] Show Financial Summary")
        print("[D] Delete an entry (Debt or Loan)")
        print("[X] Clear all Data")
        print("[Q] Quit and Save")

        choice = input("Enter your choice: ")

        if choice == '1': 
            print("\n--- Add New Debt ---")
            entry_label = input("Enter debt name: ")
            
            while True:
                amount_str = input("Enter a positive amount: ")
                try:
                    amount = float(amount_str)
                    if amount > 0: 
                        break
                    else: 
                        print("Amount must be positive.")
                except ValueError: 
                    print("Invalid number.")
            
            comments_input = input("Enter comments (optional): ")
            comments_to_save = comments_input if comments_input else None

            ledger_manager.add_entry(label=entry_label, amount=amount, comments=comments_to_save, entry_type="debt")

        elif choice == '2': 
            print("\n--- Make Payment ---")
            active_debts = [e for e in ledger_manager.get_all_entries() if e.status == 'active' and e.entry_type == 'debt']

            if not active_debts:
                print("There are no active debts to pay.")
                continue

            for debt in active_debts:
                rem_balance = calculate_balance_for_entry(debt, transaction_manager.get_all_transactions())
                print(f"ID: {debt.id[:8]} | Label: {debt.label:<20} | Remaining: ${rem_balance:8.2f}")
            
            target_short_id = input("\nEnter ID of the debt to pay (or 'c' to cancel): ")
            if target_short_id.lower() == 'c': 
                continue

            target_entry = next((e for e in active_debts if e.id.startswith(target_short_id)), None)
            
            if target_entry is None:
                print("Error: No active debt found with that ID.")
                continue
            
            while True:
                amount_str = input(f"Enter amount to pay for '{target_entry.label}': ")
                try:
                    amount = float(amount_str)
                    if amount > 0: 
                        break
                    else: 
                        print("Amount must be positive.")
                except ValueError: 
                    print("Invalid number.")

            comments_input = input("Enter comments (optional): ")
            comments_to_save = comments_input if comments_input else None

            transaction_manager.add_transaction(entry_id=target_entry.id, amount=amount, label=target_entry.label, comments=comments_to_save, transaction_type="payment")
            print(f"Successfully paid ${amount:.2f}.")

            all_transactions = transaction_manager.get_all_transactions()
            new_balance = calculate_balance_for_entry(target_entry, all_transactions)
            if new_balance <= 0:
                target_entry.status = "paid"
                print(f"\n--- Congratulations! '{target_entry.label}' has been paid off! ---")

        elif choice == '3': 
            print("\n--- Add New Loan ---")
            entry_label = input("Enter loan name: ")
            
            while True:
                amount_str = input("Enter a positive amount: ")
                try:
                    amount = float(amount_str)
                    if amount > 0: 
                        break
                    else: 
                        print("Amount must be positive.")
                except ValueError: 
                    print("Invalid number.")
            
            comments_input = input("Enter comments (optional): ")
            comments_to_save = comments_input if comments_input else None

            ledger_manager.add_entry(label=entry_label, amount=amount, comments=comments_to_save, entry_type="loan")

        elif choice == '4': 
            print("\n--- Receive a Repayment for a Loan ---")
            active_loans = [e for e in ledger_manager.get_all_entries() if e.status == 'active' and e.entry_type == 'loan']

            if not active_loans:
                print("There are no active loans to receive repayments on.")
                continue

            for loan in active_loans:
                rem_balance = calculate_balance_for_entry(loan, transaction_manager.get_all_transactions())
                print(f"ID: {loan.id[:8]} | Label: {loan.label:<20} | Remaining: ${rem_balance:8.2f}")
            
            target_short_id = input("\nEnter ID of the loan you received a repayment (or 'c' to cancel): ")
            if target_short_id.lower() == 'c': 
                continue

            target_entry = next((e for e in active_loans if e.id.startswith(target_short_id)), None)
            
            if target_entry is None:
                print("Error: No active loans found with that ID.")
                continue
            
            while True:
                amount_str = input(f"Enter the repayment amount received for '{target_entry.label}': ")
                try:
                    amount = float(amount_str)
                    if amount > 0: 
                        break
                    else: 
                        print("Amount must be positive.")
                except ValueError: 
                    print("Invalid number.")

            comments_input = input("Enter comments (optional): ")
            comments_to_save = comments_input if comments_input else None

            transaction_manager.add_transaction(entry_id=target_entry.id, amount=amount, label=target_entry.label, comments=comments_to_save, transaction_type = "repayment")
            print(f"Successfully received a repayment of ${amount:.2f}.")

            all_transactions = transaction_manager.get_all_transactions()
            new_balance = calculate_balance_for_entry(target_entry, all_transactions)
            if new_balance <= 0:
                target_entry.status = "paid"
                print(f"\n--- Congratulations! '{target_entry.label}' has been paid off! ---")

        elif choice.lower() == 'l':
            print("\n--- All Ledger Entries (Debts & Loans) ---")
            all_entries = ledger_manager.get_all_entries()
            all_transactions = transaction_manager.get_all_transactions()

            if not all_entries:
                print("No entries recorded.")
            else:
                for entry in sorted(all_entries, key=lambda e: e.date_incurred):
                    status = f"[{entry.status.upper()}]"
                    entry_type_disp = f"({entry.entry_type.capitalize()})"
                    
                    print(f"\n{status:<9} {entry_type_disp:<7} ID: {entry.id[:8]} | Label: {entry.label}")
                    print(f"      Amount: ${entry.amount:,.2f} | Date: {entry.date_incurred.strftime('%Y-%m-%d')}")

                    if entry.status == 'active':
                        eta_string = calculate_entry_eta(entry, all_transactions)
                        print(f"      -> ETA: {eta_string}")
                    if entry.comments:
                        print(f"      -> Comments: {entry.comments}")

            print("\n\n--- All Transactions (Payments & Repayments) ---")
            if not all_transactions:
                print("No transactions recorded.")
            else:
                for trans in sorted(all_transactions, key=lambda t: t.date_paid):
                    parent_entry = ledger_manager.get_entry_by_id(trans.entry_id)
                    trans_type = "Payment on Debt" if parent_entry and parent_entry.entry_type == 'debt' else "Repayment on Loan"
                    
                    print(f"\n  {trans.date_paid.strftime('%Y-%m-%d')} | ${trans.amount:7.2f} | {trans_type}")
                    print(f"      Towards: '{trans.label}' (Entry ID: {trans.entry_id[:8]})")
                    if trans.comments:
                        print(f"      -> Comments: {trans.comments}")

        elif choice.lower() == 's':
            print("\n--- Financial Summary ---")
            all_entries = ledger_manager.get_all_entries()
            all_transactions = transaction_manager.get_all_transactions()

            debt_entries = [e for e in all_entries if e.entry_type == 'debt']
            payment_transactions = [t for t in all_transactions if ledger_manager.get_entry_by_id(t.entry_id) and ledger_manager.get_entry_by_id(t.entry_id).entry_type == 'debt']
            
            total_debt = calculate_total_entry_amount(debt_entries)
            total_paid = calculate_total_transaction_amount(payment_transactions)
            debt_balance = calculate_overall_balance(total_debt, total_paid)

            print("\n-- Debts (Money You Owe) --")
            print(f"  Total Debt Incurred: ${total_debt:,.2f}")
            print(f"  Total Payments Made:  ${total_paid:,.2f}")
            print(f"  Remaining Debt:       ${debt_balance:,.2f}")
            if debt_balance > 0:
                debt_eta_string = calculate_overall_eta(debt_entries, payment_transactions)
                print(f"  {debt_eta_string}")

            loan_entries = [e for e in all_entries if e.entry_type == 'loan']
            repayment_transactions = [t for t in all_transactions if ledger_manager.get_entry_by_id(t.entry_id) and ledger_manager.get_entry_by_id(t.entry_id).entry_type == 'loan']

            total_loaned = calculate_total_entry_amount(loan_entries)
            total_repaid = calculate_total_transaction_amount(repayment_transactions)
            loan_balance = calculate_overall_balance(total_loaned, total_repaid)

            print("\n-- Loans (Money Owed To You) --")
            print(f"  Total Loaned Out:     ${total_loaned:,.2f}")
            print(f"  Total Repaid To You:  ${total_repaid:,.2f}")
            print(f"  Remaining to Collect: ${loan_balance:,.2f}")

            net_position = loan_balance - debt_balance
            print("\n-----------------------------")
            print(f"  Net Financial Position: ${net_position:,.2f}")
            print("-----------------------------")

        elif choice.lower() == 'd':
            print("\n--- Delete an Entry ---")
            all_entries = ledger_manager.get_all_entries()
            
            if not all_entries:
                print("There are no entries to delete.")
                continue

            print("Select an entry to delete:")
            for entry in all_entries:
                entry_type_disp = f"({entry.entry_type.capitalize()})"
                print(f"ID: {entry.id[:8]} | {entry_type_disp:<7} | Label: {entry.label}")
            
            target_short_id = input("\nEnter the 8-character ID of the entry to delete (or 'c' to cancel): ")
            if target_short_id.lower() == 'c':
                continue

            target_entry = next((e for e in all_entries if e.id.startswith(target_short_id)), None)

            if target_entry is None:
                print("Error: No entry found with that ID.")
                continue
            
            confirm = input(f"This will permanently delete '{target_entry.label}' and all its associated transactions. Type DELETE to confirm: ")
            if confirm == 'DELETE':
                ledger_manager.delete_entry_by_id(target_entry.id)
                transaction_manager.delete_transactions_by_entry_id(target_entry.id)
                print(f"'{target_entry.label}' and its transactions have been deleted.")
            else:
                print("Deletion cancelled.")

        
        elif choice.lower() == 'e':
            print("\n--- Edit Menu ---")
            print("[1] A Debt or Loan")
            print("[2] A Payment or Repayment")
            print("[c] Cancel")
            sub_choice = input("What would you like to edit? ")

            if sub_choice == '1':
                all_entries = ledger_manager.get_all_entries()
            
                if not all_entries:
                    print("There are no entries to edit.")
                    continue

                print("Select an entry to edit:")
                for entry in all_entries:
                    entry_type_disp = f"({entry.entry_type.capitalize()})"
                    print(f"ID: {entry.id[:8]} | {entry_type_disp:<7} | Label: {entry.label}")

                target_short_id = input("\nEnter the 8-character ID of the entry to edit (or 'c' to cancel): ")
                if target_short_id.lower() == 'c':
                    continue

                target_entry = next((e for e in all_entries if e.id.startswith(target_short_id)), None)

                if target_entry is None:
                    print("Error: No entry found with that ID.")
                    continue
                
                while True:
                    print(f"\n--- Editing '{target_entry.label}' ({target_entry.entry_type.capitalize()}) ---")
                    print(f"  Current Amount: ${target_entry.amount:,.2f}")
                    print("[1] Edit Label")
                    print("[2] Edit Amount")
                    print("[3] Edit Comments")
                    print("[c] Finish Editing and Return to Main Menu")

                    edit_choice = input("Select a field to edit: ")

                    if edit_choice == "1":
                        while True:
                            new_label = input("Enter the new label (or 'c' to cancel edit): ")
                            if new_label.lower() == 'c':
                                break 
                            
                            if new_label.strip():
                                target_entry.label = new_label
                                print("Label updated successfully.")
                                break 
                            else:
                                print("Label cannot be empty. Please try again.")

                    elif edit_choice == "2":
                        while True:
                            new_amount_str = input("Enter the new positive amount (or 'c' to cancel edit): ")
                            if new_amount_str.lower() == 'c':
                                break 
                            
                            try:
                                new_amount = float(new_amount_str)
                                if new_amount > 0:
                                    target_entry.amount = new_amount
                                    print("Amount updated successfully.")
                                    break 
                                else:
                                    print("Amount must be a positive number.")
                            except ValueError:
                                print("Invalid input. Please enter a number.")

                    elif edit_choice == "3":
                        new_comments = input("Enter new comments (press Enter to clear, or 'c' to cancel edit): ")
                        if new_comments.lower() != 'c':
                            target_entry.comments = new_comments if new_comments else None
                            print("Comments updated successfully.")

                    elif edit_choice.lower() == "c":
                        print(f"Finished editing '{target_entry.label}'. Returning to main menu.")
                        break

                    else:
                        print("Invalid choice. Please select an option from the menu.")


            elif sub_choice == '2':
                all_transactions = transaction_manager.get_all_transactions()
            
                if not all_transactions:
                    print("There are no transactions to edit.")
                    continue

                print("Select a transaction to edit:")
                for transactions in all_transactions:
                    transaction_type_disp = f"({transaction.transaction_type.capitalize()})"
                    print(f"ID: {entry.id[:8]} | {transaction_type_disp:<7} | Label: {entry.label}")

                target_short_id = input("\nEnter the 8-character ID of the transaction to edit (or 'c' to cancel): ")
                if target_short_id.lower() == 'c':
                    continue

                target_transaction = next((e for e in all_transactions if e.id.startswith(target_short_id)), None)

                if target_transaction is None:
                    print("Error: No transaction found with that ID.")
                    continue
                
                while True:
                    print(f"\n--- Editing '{target_transaction.label}' ({target_transaction.transaction_type.capitalize()}) ---")
                    print(f"  Current Amount: ${target_transaction.amount:,.2f}")
                    print("[1] Edit Label")
                    print("[2] Edit Amount")
                    print("[3] Edit Comments")
                    print("[c] Finish Editing and Return to Main Menu")

                    edit_choice = input("Select a field to edit: ")

                    if edit_choice == "1":
                        while True:
                            new_label = input("Enter the new label (or 'c' to cancel edit): ")
                            if new_label.lower() == 'c':
                                break 
                            
                            if new_label.strip():
                                target_transaction.label = new_label
                                print("Label updated successfully.")
                                break 
                            else:
                                print("Label cannot be empty. Please try again.")

                    elif edit_choice == "2":
                        while True:
                            new_amount_str = input("Enter the new positive amount (or 'c' to cancel edit): ")
                            if new_amount_str.lower() == 'c':
                                break 
                            
                            try:
                                new_amount = float(new_amount_str)
                                if new_amount > 0:
                                    target_transaction.amount = new_amount
                                    print("Amount updated successfully.")
                                    break 
                                else:
                                    print("Amount must be a positive number.")
                            except ValueError:
                                print("Invalid input. Please enter a number.")

                    elif edit_choice == "3":
                        new_comments = input("Enter new comments (press Enter to clear, or 'c' to cancel edit): ")
                        if new_comments.lower() != 'c':
                            target_transaction.comments = new_comments if new_comments else None
                            print("Comments updated successfully.")

                    elif edit_choice.lower() == "c":
                        print(f"Finished editing '{target_transaction.label}'. Returning to main menu.")
                        break

                    else:
                        print("Invalid choice. Please select an option from the menu.")

            elif sub_choice.lower() == 'c':
                continue
            
        elif choice.lower() == 'q':
            break

    print("\n--- Saving Data ---")
    storage_manager.save_data(ledger_manager=ledger_manager, transaction_manager=transaction_manager)
    print("Goodbye!")

if __name__ == "__main__":
    main()