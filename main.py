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
    /* ============================================
       Finance Board — Production Theme (Nord)
       ============================================ */

    /* --- Foundations --- */
    QWidget {
        background-color: #2e3440;
        color: #d8dee9;
        font-size: 10pt;
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    QMainWindow { background-color: #2e3440; }
    QDialog     { background-color: #2e3440; }

    /* --- Tab Bar --- */
    QTabWidget::pane {
        border: none;
        background-color: #2e3440;
    }
    QTabBar {
        qproperty-drawBase: 0;
    }
    QTabBar::tab {
        background-color: transparent;
        color: #7b88a1;
        padding: 10px 28px;
        margin-right: 0px;
        border: none;
        border-bottom: 3px solid transparent;
        font-size: 10pt;
    }
    QTabBar::tab:selected {
        color: #88c0d0;
        border-bottom: 3px solid #88c0d0;
        font-weight: bold;
    }
    QTabBar::tab:hover:!selected {
        color: #d8dee9;
        border-bottom: 3px solid #4c566a;
    }

    /* --- Lists --- */
    QListWidget, QTextBrowser {
        background-color: #3b4252;
        border: 1px solid #3b4252;
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }
    QListWidget::item {
        padding: 10px 14px;
        border-radius: 6px;
        margin: 1px 2px;
        border: 1px solid transparent;
    }
    QListWidget::item:selected {
        background-color: rgba(94, 129, 172, 0.35);
        color: #eceff4;
        border: 1px solid #5e81ac;
    }
    QListWidget::item:hover:!selected {
        background-color: rgba(76, 86, 106, 0.3);
    }

    /* --- Labels --- */
    QLabel { color: #d8dee9; }
    QLabel#Header {
        font-size: 15pt;
        font-weight: bold;
        padding: 4px 0px;
        color: #eceff4;
        letter-spacing: 0.5px;
    }
    QLabel#SubHeader {
        font-size: 12pt;
        font-weight: bold;
        color: #eceff4;
        border-bottom: 1px solid #434c5e;
        padding-bottom: 5px;
        margin-top: 6px;
    }
    QLabel#CardTitle {
        color: #7b88a1;
        font-size: 8pt;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    QLabel#CardValue {
        color: #eceff4;
        font-size: 13pt;
        font-weight: bold;
    }

    /* --- Buttons --- */
    QPushButton {
        background-color: #3b4252;
        border: 1px solid #4c566a;
        border-radius: 6px;
        padding: 7px 16px;
        min-width: 70px;
        color: #d8dee9;
    }
    QPushButton:hover {
        background-color: #434c5e;
        border-color: #5e81ac;
        color: #eceff4;
    }
    QPushButton:pressed {
        background-color: #5e81ac;
        color: #eceff4;
    }
    QPushButton:disabled {
        background-color: #2e3440;
        color: #4c566a;
        border-color: #3b4252;
    }
    QPushButton#PrimaryBtn {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5e81ac, stop:1 #5378a0);
        border: 1px solid #5e81ac;
        color: #eceff4;
        font-weight: bold;
        padding: 8px 20px;
    }
    QPushButton#PrimaryBtn:hover {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #81a1c1, stop:1 #6d93b5);
        border-color: #81a1c1;
    }
    QPushButton#PrimaryBtn:pressed {
        background-color: #4c6e96;
    }
    QPushButton#DangerBtn {
        background-color: #bf616a;
        border-color: #bf616a;
        color: #eceff4;
    }
    QPushButton#DangerBtn:hover {
        background-color: #d08770;
        border-color: #d08770;
    }
    QPushButton#SuccessBtn {
        background-color: #a3be8c;
        border-color: #a3be8c;
        color: #2e3440;
        font-weight: bold;
    }
    QPushButton#SuccessBtn:hover {
        background-color: #b4cc9e;
        border-color: #b4cc9e;
    }

    /* --- Inputs --- */
    QLineEdit, QDoubleSpinBox, QTextEdit {
        background-color: #3b4252;
        color: #eceff4;
        border: 1px solid #434c5e;
        border-radius: 6px;
        padding: 6px 10px;
        selection-background-color: #5e81ac;
    }
    QLineEdit:focus, QTextEdit:focus, QDoubleSpinBox:focus {
        border-color: #88c0d0;
    }
    QComboBox {
        background-color: #434c5e;
        color: #eceff4;
        border: 1px solid #5e81ac;
        border-radius: 6px;
        padding: 7px 28px 7px 12px;
        selection-background-color: #5e81ac;
        min-height: 18px;
    }
    QComboBox:hover {
        border-color: #88c0d0;
        background-color: #4c566a;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 26px;
        border: none;
        background-color: #5e81ac;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }
    QComboBox::drop-down:hover {
        background-color: #81a1c1;
    }
    QComboBox::down-arrow {
        image: none;
        width: 0;
        height: 0;
    }
    QComboBox QAbstractItemView {
        background-color: #3b4252;
        border: 1px solid #4c566a;
        border-radius: 4px;
        selection-background-color: #5e81ac;
        padding: 4px;
    }

    /* --- Menus --- */
    QMenuBar {
        background-color: #2e3440;
        border-bottom: 1px solid #3b4252;
        padding: 2px 4px;
        spacing: 2px;
    }
    QMenuBar::item {
        padding: 5px 12px;
        border-radius: 4px;
        color: #7b88a1;
    }
    QMenuBar::item:selected {
        background-color: #3b4252;
        color: #eceff4;
    }
    QMenu {
        background-color: #3b4252;
        border: 1px solid #434c5e;
        border-radius: 8px;
        padding: 6px;
    }
    QMenu::item {
        padding: 7px 28px 7px 16px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #5e81ac;
        color: #eceff4;
    }
    QMenu::separator {
        height: 1px;
        background-color: #434c5e;
        margin: 4px 10px;
    }

    /* --- Scrollbars --- */
    QScrollBar:vertical {
        background-color: transparent;
        width: 8px;
        margin: 2px;
    }
    QScrollBar::handle:vertical {
        background-color: #4c566a;
        border-radius: 4px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover { background-color: #5e81ac; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar:horizontal {
        background-color: transparent;
        height: 8px;
        margin: 2px;
    }
    QScrollBar::handle:horizontal {
        background-color: #4c566a;
        border-radius: 4px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover { background-color: #5e81ac; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

    /* --- Status Bar --- */
    QStatusBar {
        background-color: #2e3440;
        color: #7b88a1;
        font-size: 9pt;
        border-top: 1px solid #3b4252;
        padding: 2px 8px;
    }

    /* --- Dialogs --- */
    QDialogButtonBox QPushButton { min-width: 80px; }

    /* --- Tooltips --- */
    QToolTip {
        background-color: #3b4252;
        color: #eceff4;
        border: 1px solid #434c5e;
        border-radius: 4px;
        padding: 5px 10px;
        font-size: 9pt;
    }

    /* --- Scroll Area (transparent) --- */
    QScrollArea { border: none; background-color: transparent; }
    QScrollArea > QWidget > QWidget { background-color: transparent; }

    /* --- Cards (dashboard) --- */
    QFrame#DashCard {
        background-color: #3b4252;
        border: 1px solid #434c5e;
        border-radius: 10px;
        border-left: 3px solid #5e81ac;
    }
    QFrame#DashCard:hover {
        border-color: #88c0d0;
        border-left: 3px solid #88c0d0;
        background-color: #3d4556;
    }

    /* --- Progress Bar --- */
    QProgressBar {
        background-color: #3b4252;
        border: 1px solid #434c5e;
        border-radius: 6px;
        height: 20px;
        text-align: center;
        color: #eceff4;
        font-size: 9pt;
    }
    QProgressBar::chunk {
        background-color: #a3be8c;
        border-radius: 5px;
    }

    /* --- Group Box --- */
    QGroupBox {
        border: 1px solid #434c5e;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 16px;
        font-weight: bold;
        color: #88c0d0;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
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