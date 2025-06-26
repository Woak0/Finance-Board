from Backend.core.ledger_manager import LedgerEntry, LedgerManager
from Backend.core.transaction_manager import Transaction, TransactionManager
from Backend.storage.storage_manager import StorageManager
from Backend.core.tag_manager import TagManager
from Backend.core.journal_manager import JournalEntry, JournalManager
from Backend.core.net_worth_manager import NetWorthSnapshot, NetWorthManager
from Backend.core.ai_analyser import FinancialAnalyser
from Backend.ui_helpers import *
from Backend.utils.validators import *
from Backend.core.config_manager import load_config, save_config

def main():
    # --- First-Time Setup for API Key ---
    config = load_config()
    api_key = config.get("OPENROUTER_API_KEY")

    if not api_key:
        print("\n--- First-Time AI Setup ---")
        print("To enable AI features, you need a free API key from OpenRouter.ai.")
        user_key_input = input("Please paste your key now, or press Enter to skip: ")
        
        if user_key_input.strip():
            api_key = user_key_input.strip()
            config["OPENROUTER_API_KEY"] = api_key
            save_config(config)
            print("API Key saved! AI features are now enabled.")
        else:
            print("Setup skipped. AI features will be disabled.")
            config["OPENROUTER_API_KEY"] = None
            save_config(config)

    # --- Startup ---
    storage_manager = StorageManager()
    ledger_manager = LedgerManager()
    transaction_manager = TransactionManager()
    tag_manager = TagManager()
    journal_manager = JournalManager()
    net_worth_manager = NetWorthManager()
    ai_analyser = FinancialAnalyser(api_key=api_key)

    # Hydrate data from file
    all_data = storage_manager.load_data()
    ledger_manager.entries = [LedgerEntry.from_dict(d) for d in all_data["ledger_entries"]]
    transaction_manager.transactions = [Transaction.from_dict(t) for t in all_data["transactions"]]
    journal_manager.entries = [JournalEntry.from_dict(j) for j in all_data["journal_entries"]]
    net_worth_manager.snapshots = [NetWorthSnapshot.from_dict(n) for n in all_data["net_worth_snapshots"]]

    print("Welcome to your Financial Co-Pilot!")
    print(f"Loaded {len(ledger_manager.entries)} entries, {len(transaction_manager.transactions)} transactions, {len(journal_manager.entries)} journal entries, and {len(net_worth_manager.snapshots)} net worth snapshots.")

    # --- Main Application Loop ---
    while True:
        print("\n--- Main Menu ---")
        print("[1] Add Debt     | [2] Add Loan       | [3] Make Payment | [4] Receive Repayment")
        print("[L] List All     | [E] Edit Entry     | [D] Delete Entry | [X] Clear All Data")
        print("[S] Summary      | [P] Export to CSV")
        print("\n--- Advanced Tools ---")
        print("[A] Analyze Debt | [N] Log Net Worth  | [J] Journal      | [W] What-If Calc | [O] AI Assistant")
        print("[Q] Quit and Save")

        choice = input("Enter your choice: ").lower()

        # --- Basic Operations ---
        if choice == '1': handle_add_entry(ledger_manager, tag_manager, "debt")
        elif choice == '2': handle_add_entry(ledger_manager, tag_manager, "loan")
        elif choice == '3': handle_add_transaction(ledger_manager, transaction_manager, tag_manager, "payment")
        elif choice == '4': handle_add_transaction(ledger_manager, transaction_manager, tag_manager, "repayment")

        # --- CRUD & Listing ---
        elif choice == 'l': handle_list_all(ledger_manager, transaction_manager)
        elif choice == 'e': handle_edit_entry_main(ledger_manager, transaction_manager, tag_manager)
        elif choice == 'd': handle_delete_entry(ledger_manager, transaction_manager)
        elif choice == 'x': handle_clear_all_data(ledger_manager, transaction_manager, journal_manager, net_worth_manager)

        # --- Summary & Export ---
        elif choice == 's': handle_show_summary(ledger_manager, transaction_manager)
        elif choice == 'p': handle_export_data(ledger_manager, transaction_manager)

        # --- Advanced Tools ---
        elif choice == 'a': handle_debt_prioritization(ledger_manager, transaction_manager)
        elif choice == 'n': handle_net_worth_snapshot(ledger_manager, transaction_manager, net_worth_manager)
        elif choice == 'j': handle_journal(journal_manager)
        elif choice == 'w': handle_what_if_scenario(ledger_manager, transaction_manager)
        elif choice == 'o': handle_ai_assistant_menu(ai_analyser, ledger_manager, transaction_manager)

        # --- System ---
        elif choice == 'q': break
        else: print("Invalid choice.")

    # --- Shutdown --- 
    print("\n--- Saving Data ---")
    storage_manager.save_data(ledger_manager, transaction_manager, journal_manager, net_worth_manager)
    print("Goodbye!")

if __name__ == "__main__":
    main()