import sys
from Frontend.gui import MainWindow
from PyQt6.QtWidgets import QApplication
from Backend.storage.storage_manager import StorageManager
from Backend.core.ledger_manager import LedgerManager, LedgerEntry
from Backend.core.transaction_manager import TransactionManager, Transaction
from Backend.core.journal_manager import JournalManager, JournalEntry
from Backend.core.net_worth_manager import NetWorthManager, NetWorthSnapshot
from Backend.core.tag_manager import TagManager
from Backend.core.config_manager import load_config

DARK_STYLESHEET = """
    QWidget { background-color: #2e3440; color: #d8dee9; font-size: 10pt; font-family: 'Segoe UI'; }
    QMainWindow, QDialog { background-color: #2e3440; }
    QTabWidget::pane { border: 1px solid #434c5e; }
    QTabBar::tab { background-color: #3b4252; color: #d8dee9; padding: 10px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
    QTabBar::tab:selected { background-color: #434c5e; color: #eceff4; }
    QListWidget, QTextBrowser { background-color: #3b4252; border: 1px solid #4c566a; border-radius: 4px; padding: 5px; }
    QListWidget::item { padding: 8px; border-radius: 2px; }
    QListWidget::item:selected { background-color: #88c0d0; color: #2e3440; }
    QLabel { color: #d8dee9; }
    QLabel#Header { font-size: 18pt; font-weight: bold; padding-bottom: 10px; color: #eceff4; }
    QLabel#SubHeader { font-size: 14pt; font-weight: bold; margin-top: 10px; color: #eceff4; border-bottom: 1px solid #4c566a; padding-bottom: 5px; }
    QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4c566a, stop:1 #434c5e); border: 1px solid #4c566a; border-radius: 4px; padding: 8px; min-width: 90px; }
    QPushButton:hover { background-color: #5e81ac; }
    QPushButton:pressed { background-color: #81a1c1; }
    QPushButton:disabled { background-color: #3b4252; color: #4c566a; border: 1px solid #434c5e; }
    QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit { background-color: #434c5e; color: #eceff4; border: 1px solid #4c566a; border-radius: 4px; padding: 5px; }
    QComboBox::drop-down { border: 0px; }
    QMenuBar { background-color: #3b4252; }
    QMenuBar::item:selected { background-color: #4c566a; }
    QMenu { background-color: #3b4252; border: 1px solid #4c566a; }
    QMenu::item:selected { background-color: #88c0d0; color: #2e3440; }
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)

    config = load_config()
    
    storage = StorageManager()
    ledger_manager = LedgerManager()
    transaction_manager = TransactionManager()
    journal_manager = JournalManager()
    net_worth_manager = NetWorthManager()
    tag_manager = TagManager()

    all_data = storage.load_data()
    ledger_manager.entries = [LedgerEntry.from_dict(d) for d in all_data.get("ledger_entries", [])]
    transaction_manager.transactions = [Transaction.from_dict(t) for t in all_data.get("transactions", [])]
    journal_manager.entries = [JournalEntry.from_dict(j) for j in all_data.get("journal_entries", [])]
    net_worth_manager.snapshots = [NetWorthSnapshot.from_dict(n) for n in all_data.get("net_worth_snapshots", [])]

    window = MainWindow(
        ledger_manager=ledger_manager,
        transaction_manager=transaction_manager,
        journal_manager=journal_manager,
        net_worth_manager=net_worth_manager,
        tag_manager=tag_manager,
        storage_manager=storage,
        config=config
    )
    window.show()
    sys.exit(app.exec())