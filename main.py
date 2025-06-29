from Frontend.gui import MainWindow
from PyQt6.QtWidgets import QApplication, QMainWindow, QLayout
import sys
from Backend.core.ledger_manager import LedgerEntry, LedgerManager
from Backend.storage.storage_manager import StorageManager
from Backend.core.transaction_manager import Transaction, TransactionManager
from Backend.utils.debug_helpers import populate_with_test_data

if __name__ == "__main__":

    storage = StorageManager()
    ledger_manager = LedgerManager()
    transaction_manager = TransactionManager()

    all_data = storage.load_data()
    ledger_manager.entries = [LedgerEntry.from_dict(d) for d in all_data.get("ledger_entries", [])]
    transaction_manager.transactions = [Transaction.from_dict(t) for t in all_data.get("transactions", [])]

    all_ledger_entries = ledger_manager.get_all_entries()
    all_transactions = transaction_manager.get_all_transactions()

    if not all_ledger_entries:
        populate_with_test_data(ledger_manager, transaction_manager)
        all_ledger_entries = ledger_manager.get_all_entries()


    app = QApplication(sys.argv)

    window = MainWindow(ledger_entries=all_ledger_entries)

    window.show()

    sys.exit(app.exec())