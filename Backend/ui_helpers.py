from Backend.utils.validators import get_string_input, get_positive_float_input
from Backend.core.ledger_manager import LedgerManager, LedgerEntry
from Backend.core.transaction_manager import TransactionManager, Transaction
from Backend.core.tag_manager import TagManager, handle_edit_tags_ui
from Backend.storage.storage_manager import StorageManager
from Backend.core.export_manager import export_data_to_csv
from Backend.core.summary_calculator import (
    calculate_total_entry_amount,
    calculate_total_transaction_amount,
    calculate_overall_balance,
    calculate_balance_for_entry,
    get_transactions_for_entry,
    calculate_entry_eta,
    calculate_overall_eta,
)

storage_manager = StorageManager()
ledger_manager = LedgerManager()
transaction_manager = TransactionManager()
tag_manager = TagManager()

def update_entry_status(entry: LedgerEntry, transaction_manager: TransactionManager):
    """Checks and updates an entry's status based on its balance."""
    balance = calculate_balance_for_entry(entry, transaction_manager.get_all_transactions())
    
    status_changed = False
    if balance <= 0 and entry.status == 'active':
        entry.status = 'paid'
        status_changed = True
    elif balance > 0 and entry.status == 'paid':
        entry.status = 'active'
        status_changed = True
        
    if status_changed:
        print(f"\n--- Status Update: '{entry.label}' has been marked as [{entry.status.upper()}]. ---")

def _handle_get_tags(tag_manager: TagManager) -> list[str] | None:
    """A helper to handle the complete tag selection process."""
    print("\n--- Select Standard Tags ---")
    standard_tags = tag_manager.get_standard_tags()
    for i, tag in enumerate(standard_tags): print(f"  [{i+1}] {tag}")
    
    selection_input = get_string_input("Enter tag numbers, comma-separated (optional)", allow_empty=True)
    if selection_input is None: return None # User cancelled

    final_tags = []
    if selection_input:
        for num_str in selection_input.split(','):
            try:
                num = int(num_str.strip())
                if 1 <= num <= len(standard_tags):
                    tag_to_add = standard_tags[num - 1]
                    
                    if tag_to_add == "Other (Specify Custom)":
                        custom_tag = get_string_input("  -> Please specify your custom tag")
                        if custom_tag: final_tags.append(f"other:{custom_tag}")
                    else:
                        final_tags.append(tag_to_add)
                else:
                    print(f"Warning: Tag number '{num}' is out of range.")
            except ValueError:
                pass 
    
    return list(set(final_tags))

def handle_add_entry(ledger_manager: LedgerManager, tag_manager: TagManager, entry_type: str):
    """Handles the UI flow for adding a new debt or loan."""
    print(f"\n--- Add New {entry_type.capitalize()} ---")
    
    label = get_string_input(f"Enter {entry_type} name")
    if label is None: return

    amount = get_positive_float_input("Enter a positive amount")
    if amount is None: return
    
    print("\n--- Select Standard Tags ---")
    standard_tags = tag_manager.get_standard_tags()
    for i, tag in enumerate(standard_tags): print(f"  [{i+1}] {tag}")
    
    tag_nums_str = get_string_input("Enter tag numbers, comma-separated (optional)", allow_empty=True)
    final_tags = []
    if tag_nums_str is not None:
        for num_str in tag_nums_str.split(','):
            try:
                num = int(num_str.strip())
                if 1 <= num <= len(standard_tags):
                    final_tags.append(standard_tags[num - 1])
            except ValueError:
                pass
    
    custom_tags_str = get_string_input("Enter custom tags, comma-separated (optional)", allow_empty=True)
    if custom_tags_str:
        custom_tags = [tag.strip() for tag in custom_tags_str.split(',')]
        final_tags.extend([f"other:{tag}" for tag in custom_tags if tag])

    comments = get_string_input("Enter comments (optional)", allow_empty=True)
    if comments is None: return

    ledger_manager.add_entry(label=label, amount=amount, entry_type=entry_type, comments=comments, tags=list(set(final_tags)))

def handle_add_transaction(ledger_manager: LedgerManager, transaction_manager: TransactionManager, transaction_type: str):
    """Handles adding a payment to a debt or a repayment for a loan."""
    entry_type = "debt" if transaction_type == "payment" else "loan"
    print(f"\n--- Record a {transaction_type.capitalize()} on a {entry_type.capitalize()} ---")

    active_entries = [e for e in ledger_manager.get_all_entries() if e.status == 'active' and e.entry_type == entry_type]
    if not active_entries:
        print(f"There are no active {entry_type}s to process a {transaction_type} for.")
        return

    print(f"Select an active {entry_type} to apply this {transaction_type} to:")
    for entry in active_entries:
        rem_balance = calculate_balance_for_entry(entry, transaction_manager.get_all_transactions())
        print(f"ID: {entry.id[:8]} | Label: {entry.label:<20} | Remaining: ${rem_balance:8,.2f}")
    
    target_short_id = get_string_input(f"\nEnter ID of the {entry_type}")
    if target_short_id is None: return

    target_entry = next((e for e in active_entries if e.id.startswith(target_short_id)), None)
    if target_entry is None:
        print(f"Error: No active {entry_type} found with that ID.")
        return

    amount = get_positive_float_input(f"Enter {transaction_type} amount for '{target_entry.label}'")
    if amount is None: return
    
    label = get_string_input(f"Enter a label for this {transaction_type}")
    if label is None: return

    comments = get_string_input("Enter comments (optional)", allow_empty=True)
    if comments is None: return
    
    transaction_manager.add_transaction(entry_id=target_entry.id, amount=amount, label=label, comments=comments, transaction_type=transaction_type, tags=[])
    update_entry_status(target_entry, transaction_manager)
    print(f"Successfully recorded a {transaction_type} of ${amount:.2f}.")

    new_balance = calculate_balance_for_entry(target_entry, transaction_manager.get_all_transactions())
    if new_balance <= 0:
        target_entry.status = "paid"
        print(f"\n--- Congratulations! '{target_entry.label}' has been fully settled! ---")

# --- Display Helpers ---

def handle_list_all(ledger_manager: LedgerManager, transaction_manager: TransactionManager):
    """Displays all ledger entries and transactions."""
    all_entries = ledger_manager.get_all_entries()
    all_transactions = transaction_manager.get_all_transactions()

    print("\n--- All Ledger Entries (Debts & Loans) ---")
    if not all_entries:
        print("No entries recorded.")
    else:
        for entry in sorted(all_entries, key=lambda e: e.date_incurred):
            status = f"[{entry.status.upper()}]"
            entry_type_disp = f"({entry.entry_type.capitalize()})"
            print(f"\n{status:<9} {entry_type_disp:<7} ID: {entry.id[:8]} | Label: {entry.label}")
            print(f"      Amount: ${entry.amount:,.2f} | Date: {entry.date_incurred.strftime('%Y-%m-%d')}")
            if entry.tags: print(f"      -> Tags: {', '.join(entry.tags)}")
            if entry.status == 'active': print(f"      -> ETA: {calculate_entry_eta(entry, all_transactions)}")
            if entry.comments: print(f"      -> Comments: {entry.comments}")

    print("\n\n--- All Transactions (Payments & Repayments) ---")
    if not all_transactions:
        print("No transactions recorded.")
    else:
        for trans in sorted(all_transactions, key=lambda t: t.date_paid):
            trans_type_display = "Payment on Debt" if trans.transaction_type == "payment" else "Repayment on Loan"
            print(f"\n  {trans.date_paid.strftime('%Y-%m-%d')} | ${trans.amount:7.2f} | {trans_type_display}")
            print(f"      Towards: '{trans.label}' (Entry ID: {trans.entry_id[:8]})")
            if trans.tags: print(f"      -> Tags: {', '.join(trans.tags)}")
            if trans.comments: print(f"      -> Comments: {trans.comments}")

def handle_show_summary(ledger_manager: LedgerManager, transaction_manager: TransactionManager):
    """Calculates and displays the full financial summary."""
    print("\n--- Financial Summary ---")
    all_entries = ledger_manager.get_all_entries()
    all_transactions = transaction_manager.get_all_transactions()
    
    debt_entries = [e for e in all_entries if e.entry_type == 'debt']
    payment_transactions = [t for t in all_transactions if t.transaction_type == 'payment']
    total_debt = calculate_total_entry_amount(debt_entries)
    total_paid = calculate_total_transaction_amount(payment_transactions)
    debt_balance = total_debt - total_paid

    print("\n-- Debts (Money You Owe) --")
    print(f"  Total Debt Incurred: ${total_debt:,.2f}")
    print(f"  Total Payments Made:  ${total_paid:,.2f}")
    print(f"  Remaining Debt:       ${debt_balance:,.2f}")
    if debt_balance > 0:
        print(f"  {calculate_overall_eta(debt_entries, payment_transactions)}")

    loan_entries = [e for e in all_entries if e.entry_type == 'loan']
    repayment_transactions = [t for t in all_transactions if t.transaction_type == 'repayment']
    total_loaned = calculate_total_entry_amount(loan_entries)
    total_repaid = calculate_total_transaction_amount(repayment_transactions)
    loan_balance = total_loaned - total_repaid

    print("\n-- Loans (Money Owed To You) --")
    print(f"  Total Loaned Out:     ${total_loaned:,.2f}")
    print(f"  Total Repaid To You:  ${total_repaid:,.2f}")
    print(f"  Remaining to Collect: ${loan_balance:,.2f}")

    net_position = loan_balance - debt_balance
    print("\n-----------------------------")
    print(f"  Net Financial Position: ${net_position:,.2f}")
    print("-----------------------------")

# --- CRUD Helpers ---

def handle_delete_entry(ledger_manager: LedgerManager, transaction_manager: TransactionManager):
    """Handles the UI flow for deleting an entry and its transactions."""
    print("\n--- Delete an Entry ---")
    all_entries = ledger_manager.get_all_entries()
    if not all_entries:
        print("There are no entries to delete.")
        return

    print("Select an entry to delete:")
    for entry in all_entries:
        print(f"ID: {entry.id[:8]} | ({entry.entry_type.capitalize()}) | Label: {entry.label}")
    
    target_short_id = get_string_input("\nEnter the 8-character ID")
    if target_short_id is None: return

    target_entry = next((e for e in all_entries if e.id.startswith(target_short_id)), None)
    if target_entry is None:
        print("Error: No entry found with that ID.")
        return
    
    confirm = get_string_input(f"This will permanently delete '{target_entry.label}' and all its transactions. Type DELETE to confirm")
    if confirm == 'DELETE':
        ledger_manager.delete_entry_by_id(target_entry.id)
        transaction_manager.delete_transactions_by_entry_id(target_entry.id)
        print(f"'{target_entry.label}' has been deleted.")

def handle_clear_all_data(ledger_manager: LedgerManager, transaction_manager: TransactionManager):
    """Handles the confirmation and clearing of all data."""
    confirm = get_string_input("WARNING! This will delete all data. Type DELETE to confirm")
    if confirm == 'DELETE':
        ledger_manager.entries.clear()
        transaction_manager.transactions.clear()
        print("All data has been cleared.")

# --- THE COMPLETE EDIT LOGIC ---

def _edit_ledger_entry(ledger_manager: LedgerManager, transaction_manager: TransactionManager, tag_manager: TagManager):
    """Private helper to handle the specific UI logic for editing a LedgerEntry."""
    all_entries = ledger_manager.get_all_entries()
    if not all_entries:
        print("There are no entries to edit.")
        return

    print("Select an entry to edit:")
    for entry in all_entries:
        print(f"ID: {entry.id[:8]} | ({entry.entry_type.capitalize()}) | Label: {entry.label}")

    target_short_id = get_string_input("\nEnter the 8-character ID of the entry to edit")
    if target_short_id is None: return

    target_entry = next((e for e in all_entries if e.id.startswith(target_short_id)), None)
    if target_entry is None:
        print("Error: No entry found with that ID.")
        return
    
    while True:
        print(f"\n--- Editing '{target_entry.label}' ({target_entry.entry_type.capitalize()}) ---")
        print(f"  Current Amount: ${target_entry.amount:,.2f}")
        print("[1] Edit Label, [2] Edit Amount, [3] Edit Comments, [4] Edit Tags")
        print("[c] Finish Editing")

        edit_choice = get_string_input("Select an option")
        if edit_choice is None: break

        if edit_choice == "1":
            new_label = get_string_input(f"Enter the new label for '{target_entry.label}'")
            if new_label is not None:
                target_entry.label = new_label
                print("Label updated successfully.")
        elif edit_choice == "2":
            new_amount = get_positive_float_input("Enter the new positive amount")
            if new_amount is not None:
                target_entry.amount = new_amount
                print("Amount updated successfully.")
                update_entry_status(target_entry, transaction_manager)
        elif edit_choice == "3":
            new_comments = get_string_input("Enter new comments (press Enter to clear)", allow_empty=True)
            if new_comments is not None:
                target_entry.comments = new_comments if new_comments else None
                print("Comments updated successfully.")
        elif edit_choice == "4":
            handle_edit_tags_ui(target_entry, tag_manager)
        elif edit_choice.lower() == "c":
            print(f"Finished editing '{target_entry.label}'.")
            break
        else:
            print("Invalid choice.")

def _edit_transaction(ledger_manager: LedgerManager, transaction_manager: TransactionManager, tag_manager: TagManager):
    """Private helper to handle the specific UI logic for editing a Transaction."""
    all_transactions = transaction_manager.get_all_transactions()
    if not all_transactions:
        print("There are no transactions to edit.")
        return

    print("Select a transaction to edit:")
    for t in sorted(all_transactions, key=lambda t: t.date_paid):
        print(f"ID: {t.id[:8]} | Date: {t.date_paid.strftime('%Y-%m-%d')} | Label: {t.label} | Amount: ${t.amount:,.2f}")
    
    target_short_id = get_string_input("\nEnter the 8-character ID of the transaction to edit")
    if target_short_id is None: return

    target_transaction = next((t for t in all_transactions if t.id.startswith(target_short_id)), None)
    if target_transaction is None:
        print("Error: No transaction found with that ID.")
        return

    while True:
        print(f"\n--- Editing '{target_transaction.label}' ({target_transaction.transaction_type.capitalize()}) ---")
        print(f"  Current Amount: ${target_transaction.amount:,.2f}")
        print("[1] Edit Label, [2] Edit Amount, [3] Edit Comments, [4] Edit Tags")
        print("[c] Finish Editing")
        
        edit_choice = get_string_input("Select an option")
        if edit_choice is None: break

        if edit_choice == "1":
            new_label = get_string_input(f"Enter new label for '{target_transaction.label}'")
            if new_label is not None:
                target_transaction.label = new_label
                print("Label updated.")

        elif edit_choice == "2":
            new_amount = get_positive_float_input("Enter new positive amount")
            if new_amount is not None:
                target_transaction.amount = new_amount
                print("Amount updated.")
                parent_id = target_transaction.entry_id
                parent_entry = ledger_manager.get_entry_by_id(parent_id)
                if parent_entry:
                    update_entry_status(parent_entry, transaction_manager)

        elif edit_choice == "3":
            new_comments = get_string_input("Enter new comments (press Enter to clear)", allow_empty=True)
            if new_comments is not None:
                target_transaction.comments = new_comments if new_comments else None
                print("Comments updated.")

        elif edit_choice == "4":
            handle_edit_tags_ui(target_transaction, tag_manager)
        elif edit_choice.lower() == "c":
            print(f"Finished editing '{target_transaction.label}'.")
            break
        else:
            print("Invalid choice.")

def handle_edit_entry_main(ledger_manager: LedgerManager, transaction_manager: TransactionManager, tag_manager: TagManager):
    """The main router for the Edit menu."""
    print("\n--- Edit Menu ---")
    print("[1] A Debt or Loan")
    print("[2] A Payment or Repayment")
    
    sub_choice = get_string_input("What would you like to edit?")
    if sub_choice is None: return

    if sub_choice == '1':
        _edit_ledger_entry(ledger_manager, transaction_manager, tag_manager)
    elif sub_choice == '2':
        _edit_transaction(ledger_manager, transaction_manager, tag_manager)
    else:
        print("Invalid choice.")

def handle_export_data(ledger_manager: LedgerManager, transaction_manager: TransactionManager):
    """Handles the UI flow for exporting data."""
    print("\nExporting all data to CSV files...")
    try:
        # Call the actual export logic from the export_manager
        export_data_to_csv(ledger_manager, transaction_manager)
        print("Data export completed successfully. Check the 'Exports' directory.")
    except Exception as e:
        print(f"\nAn error occurred during export: {e}")