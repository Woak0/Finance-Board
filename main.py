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
    /* === Base === */
    QWidget {
        background-color: #2e3440;
        color: #d8dee9;
        font-size: 10pt;
        font-family: 'Segoe UI';
    }
    QMainWindow, QDialog {
        background-color: #2e3440;
    }

    /* === Tabs === */
    QTabWidget::pane {
        border: 1px solid #3b4252;
        border-radius: 6px;
        background-color: #2e3440;
    }
    QTabBar::tab {
        background-color: #3b4252;
        color: #d8dee9;
        padding: 10px 24px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-weight: 500;
    }
    QTabBar::tab:selected {
        background-color: #434c5e;
        color: #eceff4;
        border-bottom: 2px solid #88c0d0;
    }
    QTabBar::tab:hover:!selected {
        background-color: #434c5e;
    }

    /* === Lists === */
    QListWidget, QTextBrowser {
        background-color: #3b4252;
        border: 1px solid #434c5e;
        border-radius: 6px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item {
        padding: 10px 12px;
        border-radius: 4px;
        margin: 2px 4px;
    }
    QListWidget::item:selected {
        background-color: #5e81ac;
        color: #eceff4;
    }
    QListWidget::item:hover:!selected {
        background-color: #434c5e;
    }

    /* === Labels === */
    QLabel {
        color: #d8dee9;
    }
    QLabel#Header {
        font-size: 16pt;
        font-weight: bold;
        padding: 8px 0px;
        color: #eceff4;
    }
    QLabel#SubHeader {
        font-size: 13pt;
        font-weight: bold;
        color: #eceff4;
        border-bottom: 1px solid #434c5e;
        padding-bottom: 6px;
        margin-top: 8px;
    }

    /* === Buttons === */
    QPushButton {
        background-color: #434c5e;
        border: 1px solid #4c566a;
        border-radius: 6px;
        padding: 8px 16px;
        min-width: 80px;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #5e81ac;
        border-color: #5e81ac;
    }
    QPushButton:pressed {
        background-color: #81a1c1;
    }
    QPushButton:disabled {
        background-color: #3b4252;
        color: #4c566a;
        border-color: #3b4252;
    }

    /* === Inputs === */
    QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit {
        background-color: #3b4252;
        color: #eceff4;
        border: 1px solid #4c566a;
        border-radius: 6px;
        padding: 6px 10px;
        selection-background-color: #5e81ac;
    }
    QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus {
        border-color: #88c0d0;
    }
    QComboBox::drop-down {
        border: 0px;
    }

    /* === Menus === */
    QMenuBar {
        background-color: #3b4252;
        padding: 2px;
    }
    QMenuBar::item {
        padding: 6px 12px;
        border-radius: 4px;
    }
    QMenuBar::item:selected {
        background-color: #434c5e;
    }
    QMenu {
        background-color: #3b4252;
        border: 1px solid #434c5e;
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #5e81ac;
        color: #eceff4;
    }
    QMenu::separator {
        height: 1px;
        background-color: #434c5e;
        margin: 4px 8px;
    }

    /* === Scrollbars === */
    QScrollBar:vertical {
        background-color: #2e3440;
        width: 10px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical {
        background-color: #4c566a;
        border-radius: 5px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #5e81ac;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background-color: #2e3440;
        height: 10px;
        border-radius: 5px;
    }
    QScrollBar::handle:horizontal {
        background-color: #4c566a;
        border-radius: 5px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: #5e81ac;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    /* === Status Bar === */
    QStatusBar {
        background-color: #3b4252;
        color: #88c0d0;
        font-size: 9pt;
        border-top: 1px solid #434c5e;
    }

    /* === Dialog Buttons === */
    QDialogButtonBox QPushButton {
        min-width: 80px;
    }

    /* === Tooltips === */
    QToolTip {
        background-color: #3b4252;
        color: #eceff4;
        border: 1px solid #4c566a;
        border-radius: 4px;
        padding: 4px 8px;
    }
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)

    config = load_config()
    
    storage = StorageManager()
    storage.create_auto_backup()

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