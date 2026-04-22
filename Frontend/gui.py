from PyQt6.QtWidgets import *
from PyQt6.QtGui import QAction, QFont, QKeySequence, QIcon
from PyQt6.QtCore import Qt, QTimer
import copy
from datetime import datetime, timezone
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

from Backend.core.ledger_manager import LedgerManager, LedgerEntry
from Backend.core.transaction_manager import TransactionManager, Transaction
from Backend.core.journal_manager import JournalManager
from Backend.core.net_worth_manager import NetWorthManager
from Backend.core.tag_manager import TagManager
from Backend.storage.storage_manager import StorageManager
from Backend.core.export_manager import export_data_to_csv
from Backend.core.summary_calculator import *
from Backend.utils.financial_algorithms import *
from Backend.core.config_manager import save_config
from Backend.core.ai_analyser import FinancialAnalyser

# --- DIALOGS ---
class ApiKeyDialog(QDialog):
    """A dialog for the user to enter their OpenRouter.ai API key."""
    def __init__(self, current_key="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Feature Setup")
        self.setMinimumWidth(400)
        self.api_key = None

        layout = QVBoxLayout(self)
        info_label = QLabel("To enable AI features, a free API key from OpenRouter.ai is required...")
        info_label.setWordWrap(True)
        link_label = QLabel('<a href="https://openrouter.ai/keys" style="color:#88c0d0;">Open OpenRouter.ai Keys Page</a>')
        link_label.setOpenExternalLinks(True)

        self.key_input = QLineEdit()
        self.key_input.setText(current_key)
        self.key_input.setPlaceholderText("Paste your API key here (e.g., sk-or-...)")

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(info_label)
        layout.addWidget(link_label)
        layout.addWidget(self.key_input)
        layout.addWidget(button_box)

    def accept(self):
        key = self.key_input.text().strip()
        if key.startswith("sk-or-"):
            self.api_key = key
            super().accept()
        else:
            QMessageBox.warning(self, "Invalid Key", "Please enter a valid OpenRouter API key.")


class EntryDialog(QDialog):
    """A dialog for adding or editing a ledger entry (debt or loan)."""
    def __init__(self, tag_manager, entry=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Entry")
        self.entry_data = {}

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.label_input = QLineEdit(entry.label if entry else "")
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.PlusMinus)
        self.amount_input.setSingleStep(10)
        self.amount_input.setRange(0.01, 1e9)
        self.amount_input.setDecimals(2)
        self.amount_input.setValue(entry.amount if entry else 100.0)

        self.type_input = QComboBox()
        self.type_input.addItems(["debt", "loan"])
        if entry:
            self.type_input.setCurrentText(entry.entry_type)

        self.comments_input = QLineEdit(entry.comments if entry else "")

        form_layout.addRow("Label:", self.label_input)
        form_layout.addRow("Amount:", self.amount_input)
        form_layout.addRow("Type:", self.type_input)
        form_layout.addRow("Comments:", self.comments_input)
        layout.addLayout(form_layout)

        # Tags section
        tags_label = QLabel("Tags")
        tags_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(tags_label)
        self.tags_list_widget = QListWidget()
        self.tags_list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.tags_list_widget)

        all_tags = tag_manager.get_standard_tags()
        selected_tags = set(entry.tags if entry else [])
        for tag in all_tags:
            item = QListWidgetItem(tag)
            self.tags_list_widget.addItem(item)
            if tag in selected_tags:
                item.setSelected(True)
        for tag in selected_tags:
            if tag.startswith("other:"):
                item = QListWidgetItem(tag)
                self.tags_list_widget.addItem(item)
                item.setSelected(True)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def accept(self):
        if not self.label_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Label cannot be empty.")
            return

        final_tags = []
        selected_items = self.tags_list_widget.selectedItems()
        for item in selected_items:
            final_tags.append(item.text())

        self.entry_data = {
            'label': self.label_input.text().strip(),
            'amount': self.amount_input.value(),
            'entry_type': self.type_input.currentText(),
            'comments': self.comments_input.text().strip() or None,
            'tags': list(set(final_tags))
        }
        super().accept()


class TransactionDialog(QDialog):
    """A dialog for adding or editing a transaction."""
    def __init__(self, transaction_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Transaction")
        self.transaction_data = {}

        form_layout = QFormLayout(self)
        self.label_input = QLineEdit()
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.PlusMinus)
        self.amount_input.setSingleStep(10)
        self.amount_input.setRange(0.01, 1e9)
        self.amount_input.setDecimals(2)
        
        if transaction_data: # Pre-fill data if provided for editing
            self.label_input.setText(transaction_data.get('label', ''))
            self.amount_input.setValue(transaction_data.get('amount', 50.0))
        else:
            self.amount_input.setValue(50.0)

        form_layout.addRow("Label:", self.label_input)
        form_layout.addRow("Amount:", self.amount_input)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        form_layout.addRow(self.button_box)

    def accept(self):
        if not self.label_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Label cannot be empty.")
            return
        self.transaction_data = {'label': self.label_input.text().strip(), 'amount': self.amount_input.value()}
        super().accept()


class AiChatDialog(QDialog):
    """A chat window for interacting with the financial AI."""
    def __init__(self, ai_analyser, ledger_manager, transaction_manager, parent=None):
        super().__init__(parent)
        self.ai_analyser = ai_analyser
        self.ledger_manager = ledger_manager
        self.transaction_manager = transaction_manager
        self.setWindowTitle("AI Financial Chat")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)
        self.history = QTextBrowser()
        self.history.setOpenExternalLinks(True)
        layout.addWidget(self.history)

        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Ask a question...")
        self.input_line.returnPressed.connect(self.send_message)
        send_btn = QPushButton("Send")
        send_btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight)))
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)
        
        self.add_message("AI", "Hello! How can I help you analyze your finances today?")

    def add_message(self, author, text):
        self.history.append(f"<b>{author}:</b> {text.replace(chr(10), '<br>')}<br>")

    def send_message(self):
        question = self.input_line.text().strip()
        if not question:
            return
        
        self.add_message("You", question)
        self.input_line.clear()
        QApplication.processEvents()
        
        response = self.ai_analyser.answer_user_question(
            question,
            self.ledger_manager.get_all_entries(),
            self.transaction_manager.get_all_transactions()
        )
        self.add_message("AI", response)
        self.history.verticalScrollBar().setValue(self.history.verticalScrollBar().maximum())


class AiPlanEditorDialog(QDialog):
    """A dialog for reviewing and editing a plan generated by the AI."""
    def __init__(self, commands, tag_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit AI Plan")
        self.setMinimumSize(500, 400)
        self.tag_manager = tag_manager
        self.commands = copy.deepcopy(commands)

        layout = QVBoxLayout(self)
        self.command_list = QListWidget()
        self.refresh_list()
        layout.addWidget(self.command_list)
        
        btn_layout = QHBoxLayout()
        edit_btn = QPushButton("Edit Selected")
        edit_btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)))
        edit_btn.clicked.connect(self.edit_selected_command)
        
        btn_layout.addStretch()
        btn_layout.addWidget(edit_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Execute Plan")
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def refresh_list(self):
        self.command_list.clear()
        for cmd in self.commands:
            display_text = f"{cmd.get('action', '?').replace('_', ' ').title()}: {cmd.get('payload', {})}"
            self.command_list.addItem(display_text)

    def edit_selected_command(self):
        item = self.command_list.currentItem()
        if not item:
            return
            
        row = self.command_list.row(item)
        cmd = self.commands[row]

        if cmd['action'] == 'add_entry':
            temp_entry = LedgerEntry(
                label=cmd['payload'].get('label', ''),
                amount=cmd['payload'].get('amount', 0),
                entry_type=cmd['payload'].get('entry_type', 'debt'),
                tags=cmd['payload'].get('tags', [])
            )
            dialog = EntryDialog(self.tag_manager, entry=temp_entry, parent=self)
            if dialog.exec():
                self.commands[row]['payload'] = dialog.entry_data
                self.refresh_list()
        
        elif cmd['action'] == 'add_transaction':
            dialog = TransactionDialog(transaction_data=cmd['payload'], parent=self)
            if dialog.exec():
                self.commands[row]['payload'].update(dialog.transaction_data)
                self.refresh_list()
        else:
            QMessageBox.information(self, "Not Editable", f"Editing for '{cmd['action']}' actions is not yet supported.")


class WhatIfDialog(QDialog):
    """A simple dialog for the 'What-If' debt payoff calculator."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("What-If Calculator")
        self.amount = 0

        layout = QVBoxLayout(self)
        label = QLabel("Enter a hypothetical EXTRA monthly payment:")
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.PlusMinus)
        self.amount_input.setSingleStep(10)
        self.amount_input.setRange(0.01, 1e9)
        self.amount_input.setDecimals(2)
        self.amount_input.setValue(100.0)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(label)
        layout.addWidget(self.amount_input)
        layout.addWidget(button_box)

    def accept(self):
        self.amount = self.amount_input.value()
        super().accept()


# --- MAIN APPLICATION WINDOW ---

class MainWindow(QMainWindow):
    """The main application window, containing all UI elements and logic."""
    def __init__(self, **managers):
        super().__init__()
        
        for name, instance in managers.items():
            setattr(self, name, instance)

        self._undo_stack = []  # List of (type, data) tuples for undo

        self.ai_analyser = FinancialAnalyser(api_key=self.config.get("OPENROUTER_API_KEY"))
        if not self.config.get("OPENROUTER_API_KEY"):
            self.show_api_key_dialog(is_first_run=True)

        self.setWindowTitle("Finance Board")
        self.setWindowIcon(QIcon("assets/icon.ico"))
        self.setMinimumSize(1200, 800)
        self.resize(1600, 1000)
        self.setStatusBar(QStatusBar(self))
        
        self.create_menu_bar()
        self.create_tabs()
        self._setup_keyboard_shortcuts()

        self.tabs.currentChanged.connect(self.refresh_ui)
        self.refresh_ui()

    def _setup_keyboard_shortcuts(self):
        """Sets up application-wide keyboard shortcuts."""
        # Tab navigation: Ctrl+1..4
        for i in range(min(4, self.tabs.count())):
            shortcut = QAction(self)
            shortcut.setShortcut(QKeySequence(f"Ctrl+{i + 1}"))
            shortcut.triggered.connect(lambda checked, idx=i: self.tabs.setCurrentIndex(idx))
            self.addAction(shortcut)

        # Delete key for selected items
        delete_shortcut = QAction(self)
        delete_shortcut.setShortcut(QKeySequence.StandardKey.Delete)
        delete_shortcut.triggered.connect(self._handle_delete_key)
        self.addAction(delete_shortcut)

        # Ctrl+N for new entry
        new_shortcut = QAction(self)
        new_shortcut.setShortcut(QKeySequence("Ctrl+N"))
        new_shortcut.triggered.connect(self._handle_new_shortcut)
        self.addAction(new_shortcut)

    def _handle_delete_key(self):
        """Routes the Delete key to the correct delete action for the current tab."""
        tab = self.tabs.currentIndex()
        if tab == 1:
            self.delete_entry()
        elif tab == 2:
            self.delete_entry()
        elif tab == 3:
            self.delete_journal_entry()

    def _handle_new_shortcut(self):
        """Routes Ctrl+N to the correct add action for the current tab."""
        tab = self.tabs.currentIndex()
        if tab in (1, 2):
            self.add_entry()
        elif tab == 3:
            self.add_journal_entry()

    # --- UI Creation Methods ---

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        s = self.style()
        
        file_menu = menu_bar.addMenu("File")
        save_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)), "Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_and_refresh)
        export_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ArrowUp)), "Export All to CSV", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_all_data)
        api_key_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)), "Set API Key...", self)
        api_key_action.triggered.connect(self.show_api_key_dialog)
        clear_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)), "Clear All Data...", self)
        clear_action.triggered.connect(self.clear_all_data)
        backup_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)), "Backup Data...", self)
        backup_action.triggered.connect(self.backup_data)
        restore_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)), "Restore from Backup...", self)
        restore_action.triggered.connect(self.restore_data)

        file_menu.addAction(save_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(backup_action)
        file_menu.addAction(restore_action)
        file_menu.addSeparator()
        file_menu.addAction(api_key_action)
        file_menu.addSeparator()
        file_menu.addAction(clear_action)

        edit_menu = menu_bar.addMenu("Edit")
        self.undo_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ArrowBack)), "Undo Last Delete", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.setEnabled(False)
        self.undo_action.triggered.connect(self.undo_last_delete)
        edit_menu.addAction(self.undo_action)

        tools_menu = menu_bar.addMenu("Tools")
        snowball_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward)), "Debt Payoff Strategy", self)
        snowball_action.setShortcut(QKeySequence("Ctrl+D"))
        snowball_action.triggered.connect(self.show_debt_snowball)
        whatif_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)), "What-If Calculator", self)
        whatif_action.setShortcut(QKeySequence("Ctrl+W"))
        whatif_action.triggered.connect(self.show_what_if_calc)
        networth_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ToolBarVerticalExtensionButton)), "Log Net Position Snapshot", self)
        networth_action.triggered.connect(self.log_net_position)
        monthly_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileDialogListView)), "Monthly Payment Summary", self)
        monthly_action.setShortcut(QKeySequence("Ctrl+M"))
        monthly_action.triggered.connect(self.show_monthly_summary)
        tools_menu.addAction(snowball_action)
        tools_menu.addAction(whatif_action)
        tools_menu.addAction(networth_action)
        tools_menu.addSeparator()
        tools_menu.addAction(monthly_action)

        ai_menu = menu_bar.addMenu("AI Tools")
        health_check_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)), "Get Financial Health Check", self)
        health_check_action.triggered.connect(self.run_ai_health_check)
        chat_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)), "Start AI Chat", self)
        chat_action.triggered.connect(self.run_ai_chat)
        command_bar_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_CommandLink)), "Use AI Command Bar", self)
        command_bar_action.triggered.connect(self.run_ai_command_bar)
        ai_menu.addAction(health_check_action)
        ai_menu.addAction(chat_action)
        ai_menu.addAction(command_bar_action)

    def create_tabs(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(self.create_dashboard_tab(), "  Dashboard  ")
        self.tabs.addTab(self.create_ledger_tab(), "  Ledger  ")
        self.tabs.addTab(self.create_history_tab(), "  History  ")
        self.tabs.addTab(self.create_journal_tab(), "  Journal  ")

    def create_dashboard_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setSpacing(10)
        title = QLabel("Finance Board Dashboard")
        title.setObjectName("Header")
        main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)

        # --- Top row: Summary + Charts side by side ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)

        # Summary panel
        summary_container = QWidget()
        summary_layout = QFormLayout(summary_container)
        summary_layout.setContentsMargins(10, 5, 10, 5)
        self.summary_labels = {
            'debt_incurred': QLabel(), 'debt_paid': QLabel(), 'debt_remaining': QLabel(), 'debt_eta': QLabel(),
            'loan_out': QLabel(), 'loan_repaid': QLabel(), 'loan_remaining': QLabel(), 'net_position': QLabel()
        }
        for label in self.summary_labels.values():
            label.setFont(QFont("Segoe UI", 11))
        self.summary_labels['net_position'].setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))

        summary_layout.addRow(QLabel("<b>DEBTS (Money You Owe)</b>"))
        summary_layout.addRow("Total Debt Incurred:", self.summary_labels['debt_incurred'])
        summary_layout.addRow("Total Payments Made:", self.summary_labels['debt_paid'])
        summary_layout.addRow("<b>Remaining Debt Balance:</b>", self.summary_labels['debt_remaining'])
        summary_layout.addRow("<i>Est. Debt-Free Date:</i>", self.summary_labels['debt_eta'])
        summary_layout.addRow(QLabel())
        summary_layout.addRow(QLabel("<b>LOANS (Money Owed to You)</b>"))
        summary_layout.addRow("Total Loaned Out:", self.summary_labels['loan_out'])
        summary_layout.addRow("Total Repaid to You:", self.summary_labels['loan_repaid'])
        summary_layout.addRow("<b>Remaining to Collect:</b>", self.summary_labels['loan_remaining'])
        summary_layout.addRow(QLabel())
        summary_layout.addRow("<h2>Net Financial Position:</h2>", self.summary_labels['net_position'])

        # Charts stacked vertically on the right
        charts_container = QWidget()
        charts_layout = QVBoxLayout(charts_container)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(5)

        self.pie_chart_canvas = self.create_pie_chart()
        self.bar_chart_canvas = self.create_bar_chart()
        self.line_chart_canvas = self.create_line_chart()

        # Top charts side by side
        top_charts_layout = QHBoxLayout()
        top_charts_layout.setSpacing(5)
        top_charts_layout.addWidget(self.pie_chart_canvas)
        top_charts_layout.addWidget(self.bar_chart_canvas)
        charts_layout.addLayout(top_charts_layout, 1)

        top_layout.addWidget(summary_container, 2)
        top_layout.addWidget(charts_container, 3)
        main_layout.addLayout(top_layout, 2)

        # --- Middle: Quick-stats cards + Quick-add payment ---
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(10)

        # Quick-stats cards
        self.stats_cards = {}
        for key, label in [('active_debts', 'Active Debts'), ('paid_this_month', 'Paid This Month'),
                           ('biggest_debt', 'Biggest Remaining'), ('entries_paid_off', 'Settled Entries')]:
            card = QWidget()
            card.setStyleSheet("background-color: #3b4252; border-radius: 8px; padding: 8px;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            title_lbl = QLabel(label)
            title_lbl.setStyleSheet("color: #88c0d0; font-size: 9pt; font-weight: bold;")
            value_lbl = QLabel("--")
            value_lbl.setStyleSheet("font-size: 14pt; font-weight: bold;")
            card_layout.addWidget(title_lbl)
            card_layout.addWidget(value_lbl)
            self.stats_cards[key] = value_lbl
            middle_layout.addWidget(card)

        # Quick-add payment button
        quick_add_card = QWidget()
        quick_add_card.setStyleSheet("background-color: #3b4252; border-radius: 8px; padding: 8px;")
        quick_add_layout = QVBoxLayout(quick_add_card)
        quick_add_layout.setContentsMargins(12, 8, 12, 8)
        quick_add_title = QLabel("Quick Payment")
        quick_add_title.setStyleSheet("color: #88c0d0; font-size: 9pt; font-weight: bold;")
        self.quick_add_combo = QComboBox()
        self.quick_add_btn = QPushButton("Add Payment")
        self.quick_add_btn.clicked.connect(self.quick_add_payment)
        quick_add_layout.addWidget(quick_add_title)
        quick_add_layout.addWidget(self.quick_add_combo)
        quick_add_layout.addWidget(self.quick_add_btn)
        middle_layout.addWidget(quick_add_card)

        main_layout.addLayout(middle_layout, 0)

        # --- Bottom: Line chart spanning full width ---
        main_layout.addWidget(self.line_chart_canvas, 1)
        return widget
    
    def create_pie_chart(self):
        fig, self.pie_ax = plt.subplots(facecolor='#2e3440')
        self.pie_ax.set_facecolor('#2e3440')
        fig.subplots_adjust(left=0.05, right=0.70, top=0.88, bottom=0.05)
        return FigureCanvas(fig)

    def create_bar_chart(self):
        fig, self.bar_ax = plt.subplots(facecolor='#2e3440')
        self.bar_ax.set_facecolor('#2e3440')
        fig.subplots_adjust(left=0.18, right=0.95, top=0.88, bottom=0.30)
        return FigureCanvas(fig)

    def create_line_chart(self):
        fig, self.line_ax = plt.subplots(facecolor='#2e3440')
        self.line_ax.set_facecolor('#2e3440')
        fig.subplots_adjust(left=0.08, right=0.97, top=0.90, bottom=0.20)
        return FigureCanvas(fig)

    def _create_details_panel_widgets(self):
        """Factory method to create a reusable details panel."""
        s = self.style()
        container = QWidget()
        layout = QVBoxLayout(container)
        widgets = {}

        widgets['detail_label'] = QLabel("No item selected")
        widgets['detail_label'].setObjectName("SubHeader")
        widgets['detail_balance'] = QLabel()
        widgets['progress_bar'] = QProgressBar()
        widgets['progress_bar'].setTextVisible(True)
        widgets['progress_bar'].setFormat("%p% paid off")
        widgets['progress_bar'].setStyleSheet("""
            QProgressBar { background-color: #3b4252; border: 1px solid #434c5e; border-radius: 6px; height: 22px; text-align: center; color: #eceff4; }
            QProgressBar::chunk { background-color: #a3be8c; border-radius: 5px; }
        """)
        widgets['progress_bar'].setVisible(False)
        widgets['detail_info'] = QLabel()
        widgets['detail_info'].setWordWrap(True)
        widgets['detail_info'].setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(widgets['detail_label'])
        layout.addWidget(widgets['detail_balance'])
        layout.addWidget(widgets['progress_bar'])
        layout.addWidget(widgets['detail_info'])

        trans_header_layout = QHBoxLayout()
        trans_label = QLabel("Transactions")
        trans_label.setStyleSheet("font-size: 12pt; margin-top: 15px;")
        widgets['edit_transaction_btn'] = QPushButton(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)), "")
        widgets['edit_transaction_btn'].setToolTip("Edit Selected Transaction")
        widgets['edit_transaction_btn'].setEnabled(False)
        widgets['edit_transaction_btn'].clicked.connect(self.edit_transaction)
        widgets['delete_transaction_btn'] = QPushButton(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)), "")
        widgets['delete_transaction_btn'].setToolTip("Delete Selected Transaction")
        widgets['delete_transaction_btn'].setEnabled(False)
        widgets['delete_transaction_btn'].clicked.connect(self.delete_transaction)
        trans_header_layout.addWidget(trans_label)
        trans_header_layout.addStretch()
        trans_header_layout.addWidget(widgets['edit_transaction_btn'])
        trans_header_layout.addWidget(widgets['delete_transaction_btn'])
        layout.addLayout(trans_header_layout)

        widgets['transaction_list'] = QListWidget()
        widgets['transaction_list'].currentItemChanged.connect(self.on_transaction_selection_changed)
        layout.addWidget(widgets['transaction_list'], 1)

        payment_btn_layout = QHBoxLayout()
        widgets['add_payment_btn'] = QPushButton("Add Payment")
        widgets['add_payment_btn'].setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)))
        widgets['add_payment_btn'].clicked.connect(self.add_transaction)
        widgets['use_template_btn'] = QPushButton("Use Template")
        widgets['use_template_btn'].setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileDialogListView)))
        widgets['use_template_btn'].clicked.connect(self.use_transaction_template)
        widgets['use_template_btn'].setEnabled(False)
        payment_btn_layout.addWidget(widgets['add_payment_btn'])
        payment_btn_layout.addWidget(widgets['use_template_btn'])
        layout.addLayout(payment_btn_layout)

        crud_layout = QHBoxLayout()
        add_btn = QPushButton("Add Entry")
        add_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileIcon)))
        add_btn.clicked.connect(self.add_entry)
        dup_btn = QPushButton("Duplicate")
        dup_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)))
        dup_btn.clicked.connect(self.duplicate_entry)
        edit_btn = QPushButton("Edit Entry")
        edit_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)))
        edit_btn.clicked.connect(self.edit_entry)
        delete_btn = QPushButton("Delete Entry")
        delete_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)))
        delete_btn.clicked.connect(self.delete_entry)

        crud_layout.addStretch()
        crud_layout.addWidget(add_btn)
        crud_layout.addWidget(dup_btn)
        crud_layout.addWidget(edit_btn)
        crud_layout.addWidget(delete_btn)
        layout.addLayout(crud_layout)

        return container, widgets

    def create_ledger_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.addWidget(QLabel("<b>Active Debts & Loans</b>"))

        # Search bar
        self.ledger_search = QLineEdit()
        self.ledger_search.setPlaceholderText("Search entries...")
        self.ledger_search.setClearButtonEnabled(True)
        self.ledger_search.textChanged.connect(self.refresh_ledger_list)
        list_layout.addWidget(self.ledger_search)

        # Filter and sort controls
        filter_sort_layout = QHBoxLayout()
        self.ledger_filter = QComboBox()
        self.ledger_filter.addItems(["All Types", "Debts Only", "Loans Only"])
        self.ledger_filter.currentIndexChanged.connect(self.refresh_ledger_list)
        self.ledger_sort = QComboBox()
        self.ledger_sort.addItems(["Sort: A-Z", "Sort: Z-A", "Sort: Balance (Low)", "Sort: Balance (High)", "Sort: Date (Newest)", "Sort: Date (Oldest)"])
        self.ledger_sort.currentIndexChanged.connect(self.refresh_ledger_list)
        filter_sort_layout.addWidget(self.ledger_filter)
        filter_sort_layout.addWidget(self.ledger_sort)
        list_layout.addLayout(filter_sort_layout)

        self.active_list_widget = QListWidget()
        self.active_list_widget.currentItemChanged.connect(self.on_active_list_selection)
        list_layout.addWidget(self.active_list_widget)

        self.ledger_details_panel, self.ledger_widgets = self._create_details_panel_widgets()

        layout.addWidget(list_container, 1)
        layout.addWidget(self.ledger_details_panel, 2)
        return widget

    def create_history_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.addWidget(QLabel("<b>Paid & Settled History</b>"))
        self.history_list_widget = QListWidget()
        self.history_list_widget.currentItemChanged.connect(self.on_history_list_selection)
        list_layout.addWidget(self.history_list_widget)

        self.history_details_panel, self.history_widgets = self._create_details_panel_widgets()
        self.history_widgets['add_payment_btn'].setVisible(False)

        layout.addWidget(list_container, 1)
        layout.addWidget(self.history_details_panel, 2)
        return widget

    def create_journal_tab(self):
        s = self.style()
        widget = QWidget()
        main_layout = QHBoxLayout(widget)

        # --- Left panel: Notebooks ---
        notebook_panel = QWidget()
        notebook_layout = QVBoxLayout(notebook_panel)
        notebook_layout.addWidget(QLabel("<b>Notebooks</b>"))

        self.notebook_list = QListWidget()
        self.notebook_list.currentItemChanged.connect(self.on_notebook_selection_changed)
        notebook_layout.addWidget(self.notebook_list, 1)

        nb_btn_layout = QHBoxLayout()
        add_nb_btn = QPushButton("New Notebook")
        add_nb_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)))
        add_nb_btn.clicked.connect(self.add_notebook)
        self.rename_nb_btn = QPushButton("Rename")
        self.rename_nb_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)))
        self.rename_nb_btn.clicked.connect(self.rename_notebook)
        self.rename_nb_btn.setEnabled(False)
        nb_btn_layout.addWidget(add_nb_btn)
        nb_btn_layout.addWidget(self.rename_nb_btn)
        notebook_layout.addLayout(nb_btn_layout)

        # --- Right panel: Entries ---
        entry_panel = QWidget()
        entry_layout = QVBoxLayout(entry_panel)
        self.journal_header = QLabel("Financial Journal")
        self.journal_header.setObjectName("Header")
        entry_layout.addWidget(self.journal_header)

        self.journal_list = QListWidget()
        self.journal_list.setWordWrap(True)
        self.journal_list.currentItemChanged.connect(self.on_journal_selection_changed)
        entry_layout.addWidget(self.journal_list, 1)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Entry")
        add_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon)))
        add_btn.clicked.connect(self.add_journal_entry)
        self.edit_journal_btn = QPushButton("Edit Selected")
        self.edit_journal_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)))
        self.edit_journal_btn.clicked.connect(self.edit_journal_entry)
        self.edit_journal_btn.setEnabled(False)
        self.delete_journal_btn = QPushButton("Delete Selected")
        self.delete_journal_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)))
        self.delete_journal_btn.clicked.connect(self.delete_journal_entry)
        self.delete_journal_btn.setEnabled(False)

        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(self.edit_journal_btn)
        btn_layout.addWidget(self.delete_journal_btn)
        entry_layout.addLayout(btn_layout)

        main_layout.addWidget(notebook_panel, 1)
        main_layout.addWidget(entry_panel, 3)
        return widget

    # --- UI Refresh & Update Logic ---

    def refresh_ui(self, index=None):
        """Refreshes the currently active tab."""
        if index is None:
            index = self.tabs.currentIndex()
        
        if index == 0:
            self.refresh_dashboard()
        elif index == 1:
            self.refresh_ledger_list()
        elif index == 2:
            self.refresh_history_list()
        elif index == 3:
            self.refresh_journal_list()

    def refresh_dashboard(self):
        all_entries = self.ledger_manager.get_all_entries()
        all_transactions = self.transaction_manager.get_all_transactions()
        
        debt_entries = [e for e in all_entries if e.entry_type == 'debt']
        loan_entries = [e for e in all_entries if e.entry_type == 'loan']
        
        debt_balance = sum(calculate_balance_for_entry(d, all_transactions) for d in debt_entries)
        loan_balance = sum(calculate_balance_for_entry(l, all_transactions) for l in loan_entries)
        net_position = loan_balance - debt_balance
        
        total_debt = calculate_total_entry_amount(debt_entries)
        total_loaned = calculate_total_entry_amount(loan_entries)
        total_paid = calculate_total_transaction_amount([t for t in all_transactions if t.transaction_type == 'payment'])
        total_repaid = calculate_total_transaction_amount([t for t in all_transactions if t.transaction_type == 'repayment'])
        
        self.summary_labels['debt_incurred'].setText(f"<span style='color:#bf616a'>${total_debt:,.2f}</span>")
        self.summary_labels['debt_paid'].setText(f"<span style='color:#a3be8c'>${total_paid:,.2f}</span>")
        self.summary_labels['debt_remaining'].setText(f"<span style='color:#bf616a'>${debt_balance:,.2f}</span>")
        self.summary_labels['debt_eta'].setText(calculate_overall_eta(debt_entries, [t for t in all_transactions if t.transaction_type == 'payment']))
        self.summary_labels['loan_out'].setText(f"${total_loaned:,.2f}")
        self.summary_labels['loan_repaid'].setText(f"<span style='color:#a3be8c'>${total_repaid:,.2f}</span>")
        self.summary_labels['loan_remaining'].setText(f"${loan_balance:,.2f}")
        net_color = '#a3be8c' if net_position >= 0 else '#bf616a'
        self.summary_labels['net_position'].setText(f"<span style='color:{net_color}'>${net_position:,.2f}</span>")

        self.pie_ax.clear()
        self.pie_ax.set_title('Debt vs. Loans Balance', color='white')
        if debt_balance > 0 or loan_balance > 0:
            self.pie_ax.pie(
                [debt_balance, loan_balance],
                labels=['Total Debt', 'Total Loans'],
                autopct='%1.1f%%',
                startangle=90,
                colors=['#bf616a', '#a3be8c'],
                textprops={'color': 'white'}
            )
        else:
            self.pie_ax.text(0.5, 0.5, 'No Data', ha='center', va='center', color='gray')
        self.pie_chart_canvas.draw()
        
        self.bar_ax.clear()
        self.bar_ax.set_title('Totals vs. Payments', color='white')
        self.bar_ax.tick_params(axis='x', colors='white')
        self.bar_ax.tick_params(axis='y', colors='white')
        self.bar_ax.spines['bottom'].set_color('#d8dee9')
        self.bar_ax.spines['left'].set_color('#d8dee9')
        self.bar_ax.spines['top'].set_color('#2e3440')
        self.bar_ax.spines['right'].set_color('#2e3440')
        categories = ['Debts', 'Loans']
        totals = [total_debt, total_loaned]
        paids = [total_paid, total_repaid]
        x = np.arange(len(categories))
        width = 0.35
        self.bar_ax.bar(x - width / 2, totals, width, label='Total Incurred/Loaned', color='#d08770')
        self.bar_ax.bar(x + width / 2, paids, width, label='Total Paid/Repaid', color='#a3be8c')
        self.bar_ax.set_ylabel('Amount (AUD)', color='white')
        self.bar_ax.set_xticks(x, categories)
        self.bar_ax.legend(labelcolor='white', facecolor='#3b4252', edgecolor='#4c566a', bbox_to_anchor=(0.5, -0.1), loc='upper center')
        self.bar_chart_canvas.draw()
        
        self.line_ax.clear()
        self.line_ax.set_title('Net Position Over Time', color='white')
        self.line_ax.tick_params(axis='x', colors='white')
        self.line_ax.tick_params(axis='y', colors='white')
        self.line_ax.spines['bottom'].set_color('#d8dee9')
        self.line_ax.spines['left'].set_color('#d8dee9')
        self.line_ax.spines['top'].set_color('#2e3440')
        self.line_ax.spines['right'].set_color('#2e3440')
        snapshots = self.net_worth_manager.get_all_snapshots()
        if len(snapshots) > 1:
            dates = [s.date_recorded for s in snapshots]
            values = [s.net_position for s in snapshots]
            self.line_ax.plot(dates, values, marker='o', color='#88c0d0')
            self.line_ax.figure.autofmt_xdate()
        else:
            self.line_ax.text(0.5, 0.5, 'At least two snapshots needed to see a trend', ha='center', va='center', color='gray')
        self.line_chart_canvas.draw()

        # --- Quick-stats cards ---
        active_debts = [e for e in debt_entries if e.status == 'active']
        self.stats_cards['active_debts'].setText(str(len(active_debts)))

        # Paid this month
        now = datetime.now(timezone.utc)
        month_transactions = [t for t in all_transactions
                              if t.date_paid.year == now.year and t.date_paid.month == now.month]
        paid_this_month = sum(t.amount for t in month_transactions)
        self.stats_cards['paid_this_month'].setText(f"${paid_this_month:,.2f}")

        # Biggest remaining debt
        if active_debts:
            biggest = max(active_debts, key=lambda e: calculate_balance_for_entry(e, all_transactions))
            biggest_bal = calculate_balance_for_entry(biggest, all_transactions)
            self.stats_cards['biggest_debt'].setText(f"{biggest.label[:15]}\n${biggest_bal:,.2f}")
        else:
            self.stats_cards['biggest_debt'].setText("None!")

        # Settled entries count
        paid_entries = [e for e in all_entries if e.status == 'paid']
        self.stats_cards['entries_paid_off'].setText(str(len(paid_entries)))

        # --- Quick-add payment dropdown ---
        self.quick_add_combo.clear()
        active_entries = [e for e in all_entries if e.status == 'active']
        for entry in sorted(active_entries, key=lambda e: e.label):
            balance = calculate_balance_for_entry(entry, all_transactions)
            self.quick_add_combo.addItem(f"{entry.label} (${balance:,.2f})", entry)
        self.quick_add_btn.setEnabled(bool(active_entries))

    def refresh_ledger_list(self):
        current_id = self.get_selected_entry_id()
        self.active_list_widget.clear()
        selected_item_to_restore = None

        all_transactions = self.transaction_manager.get_all_transactions()

        # Filter active entries
        entries = [e for e in self.ledger_manager.get_all_entries() if e.status == 'active']

        # Apply type filter
        filter_idx = self.ledger_filter.currentIndex() if hasattr(self, 'ledger_filter') else 0
        if filter_idx == 1:
            entries = [e for e in entries if e.entry_type == 'debt']
        elif filter_idx == 2:
            entries = [e for e in entries if e.entry_type == 'loan']

        # Apply search
        search_text = self.ledger_search.text().strip().lower() if hasattr(self, 'ledger_search') else ""
        if search_text:
            entries = [e for e in entries if search_text in e.label.lower() or
                       any(search_text in tag.lower() for tag in e.tags) or
                       (e.comments and search_text in e.comments.lower())]

        # Pre-calculate balances for sorting
        entry_balances = {e.id: calculate_balance_for_entry(e, all_transactions) for e in entries}

        # Apply sort
        sort_idx = self.ledger_sort.currentIndex() if hasattr(self, 'ledger_sort') else 0
        if sort_idx == 0:
            entries.sort(key=lambda e: (e.label or '').lower())
        elif sort_idx == 1:
            entries.sort(key=lambda e: (e.label or '').lower(), reverse=True)
        elif sort_idx == 2:
            entries.sort(key=lambda e: entry_balances[e.id])
        elif sort_idx == 3:
            entries.sort(key=lambda e: entry_balances[e.id], reverse=True)
        elif sort_idx == 4:
            entries.sort(key=lambda e: e.date_incurred, reverse=True)
        elif sort_idx == 5:
            entries.sort(key=lambda e: e.date_incurred)

        for entry in entries:
            balance = entry_balances[entry.id]
            type_icon = "\u25B2" if entry.entry_type == 'loan' else "\u25BC"
            item = QListWidgetItem(f"{type_icon}  {entry.label}    ${balance:,.2f}")
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.active_list_widget.addItem(item)
            if entry and current_id and entry.id == current_id:
                selected_item_to_restore = item

        if selected_item_to_restore:
            self.active_list_widget.setCurrentItem(selected_item_to_restore)
        else:
            self._update_details_panel(None, self.ledger_widgets)
            
    def refresh_history_list(self):
        current_id = self.get_selected_entry_id()
        self.history_list_widget.clear()
        selected_item_to_restore = None

        sorted_entries = sorted(self.ledger_manager.get_all_entries(), key=lambda e: e.label or '')

        all_transactions = self.transaction_manager.get_all_transactions()
        for entry in sorted_entries:
            if entry.status == 'paid':
                type_label = "Loan" if entry.entry_type == 'loan' else "Debt"
                item = QListWidgetItem(f"\u2713  {entry.label}  ({type_label} - ${entry.amount:,.2f})")
                item.setData(Qt.ItemDataRole.UserRole, entry)
                self.history_list_widget.addItem(item)
                if entry and current_id and entry.id == current_id:
                    selected_item_to_restore = item

        if selected_item_to_restore:
            self.history_list_widget.setCurrentItem(selected_item_to_restore)
        else:
            self._update_details_panel(None, self.history_widgets)

    def refresh_journal_list(self):
        # Refresh notebook list
        current_notebook = None
        if self.notebook_list.currentItem():
            current_notebook = self.notebook_list.currentItem().text()

        self.notebook_list.clear()
        notebooks = self.journal_manager.get_notebooks()
        if not notebooks:
            notebooks = ["General"]

        notebook_to_select = None
        for nb in notebooks:
            item = QListWidgetItem(nb)
            self.notebook_list.addItem(item)
            if nb == current_notebook:
                notebook_to_select = item

        if notebook_to_select:
            self.notebook_list.setCurrentItem(notebook_to_select)
        elif self.notebook_list.count() > 0:
            self.notebook_list.setCurrentRow(0)

        self._refresh_journal_entries()

    def _refresh_journal_entries(self):
        """Refreshes the journal entry list based on the selected notebook."""
        current_id = self.get_selected_journal_id()
        self.journal_list.clear()
        self.delete_journal_btn.setEnabled(False)
        self.edit_journal_btn.setEnabled(False)

        selected_notebook = self.notebook_list.currentItem()
        if not selected_notebook:
            return

        notebook_name = selected_notebook.text()
        self.journal_header.setText(f"Journal - {notebook_name}")
        entries = self.journal_manager.get_entries_by_notebook(notebook_name)

        for entry in entries:
            item = QListWidgetItem(f"{entry.date_created.strftime('%Y-%m-%d %H:%M')}\n{entry.content}")
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.journal_list.addItem(item)
            if entry and current_id and entry.id == current_id:
                self.journal_list.setCurrentItem(item)

    def _update_details_panel(self, entry, widgets):
        """A generic function to update a details panel, given an entry and a dict of widgets."""
        widgets['transaction_list'].clear()
        widgets['delete_transaction_btn'].setEnabled(False)
        widgets['edit_transaction_btn'].setEnabled(False)

        if entry:
            widgets['add_payment_btn'].setEnabled(entry.status == 'active')
            widgets['add_payment_btn'].setText(f"Add {'Payment' if entry.entry_type == 'debt' else 'Repayment'}")
            widgets['use_template_btn'].setEnabled(entry.status == 'active' and bool(self.config.get('transaction_templates')))

            balance = calculate_balance_for_entry(entry, self.transaction_manager.get_all_transactions())
            widgets['detail_label'].setText(entry.label)
            widgets['detail_balance'].setText(f"<b>Current Balance: ${balance:,.2f}</b>")

            # Progress bar
            if entry.amount > 0:
                paid_pct = max(0, min(100, int(((entry.amount - balance) / entry.amount) * 100)))
                widgets['progress_bar'].setValue(paid_pct)
                widgets['progress_bar'].setVisible(True)
            else:
                widgets['progress_bar'].setVisible(False)

            widgets['detail_info'].setText(
                f"<b>Type:</b> {entry.entry_type.capitalize()}<br>"
                f"<b>Status:</b> {entry.status.capitalize()}<br>"
                f"<b>Original Amount:</b> ${entry.amount:,.2f}<br>"
                f"<b>Tags:</b> {', '.join(entry.tags) if entry.tags else 'None'}<br>"
                f"<b>Comments:</b> {entry.comments or 'None'}"
            )

            transactions = self.transaction_manager.get_transactions_for_entry(entry.id)
            for t in sorted(transactions, key=lambda t: t.date_paid, reverse=True):
                item = QListWidgetItem(f"{t.date_paid.strftime('%Y-%m-%d')} - {t.label} (${t.amount:,.2f})")
                item.setData(Qt.ItemDataRole.UserRole, t)
                widgets['transaction_list'].addItem(item)
        else:
            widgets['detail_label'].setText("No item selected")
            widgets['detail_balance'].setText("")
            widgets['detail_info'].setText("")
            widgets['progress_bar'].setVisible(False)
            widgets['add_payment_btn'].setEnabled(False)
            widgets['use_template_btn'].setEnabled(False)

    # --- Event Handlers / Slots ---

    def on_active_list_selection(self, current, previous):
        entry = current.data(Qt.ItemDataRole.UserRole) if current else None
        self._update_details_panel(entry, self.ledger_widgets)

    def on_history_list_selection(self, current, previous):
        entry = current.data(Qt.ItemDataRole.UserRole) if current else None
        self._update_details_panel(entry, self.history_widgets)

    def on_notebook_selection_changed(self, current, previous):
        self._refresh_journal_entries()
        can_rename = bool(current) and current.text() != "General"
        self.rename_nb_btn.setEnabled(can_rename)

    def on_journal_selection_changed(self):
        has_selection = bool(self.journal_list.currentItem())
        self.delete_journal_btn.setEnabled(has_selection)
        self.edit_journal_btn.setEnabled(has_selection)
    
    def on_transaction_selection_changed(self):
        """Enables edit/delete buttons for the correct tab's transaction list."""
        tab_index = self.tabs.currentIndex()
        if tab_index == 1:
            is_selected = bool(self.ledger_widgets['transaction_list'].currentItem())
            self.ledger_widgets['delete_transaction_btn'].setEnabled(is_selected)
            self.ledger_widgets['edit_transaction_btn'].setEnabled(is_selected)
        elif tab_index == 2:
            is_selected = bool(self.history_widgets['transaction_list'].currentItem())
            self.history_widgets['delete_transaction_btn'].setEnabled(is_selected)
            self.history_widgets['edit_transaction_btn'].setEnabled(is_selected)

    # --- Core App Logic / "CRUD" Actions ---

    def add_entry(self):
        dialog = EntryDialog(self.tag_manager, parent=self)
        if dialog.exec():
            self.ledger_manager.add_entry(**dialog.entry_data)
            self.save_and_refresh()
    
    def edit_entry(self):
        entry = self.get_selected_entry()
        if not entry:
            QMessageBox.warning(self, "No Selection", "Please select an entry to edit.")
            return
            
        dialog = EntryDialog(self.tag_manager, entry=entry, parent=self)
        if dialog.exec():
            data = dialog.entry_data
            entry.label = data['label']
            entry.amount = data['amount']
            entry.entry_type = data['entry_type']
            entry.comments = data['comments']
            entry.tags = data['tags']
            self.update_entry_status(entry)
            self.save_and_refresh()
            
    def duplicate_entry(self):
        entry = self.get_selected_entry()
        if not entry:
            QMessageBox.warning(self, "No Selection", "Please select an entry to duplicate.")
            return
        self.ledger_manager.add_entry(
            label=f"{entry.label} (Copy)",
            amount=entry.amount,
            entry_type=entry.entry_type,
            comments=entry.comments,
            tags=list(entry.tags),
        )
        self.save_and_refresh()

    def delete_entry(self):
        entry = self.get_selected_entry()
        if not entry:
            QMessageBox.warning(self, "No Selection", "Please select an entry to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", f"Delete '{entry.label}' and all its transactions?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Save to undo stack before deleting
            related_transactions = self.transaction_manager.get_transactions_for_entry(entry.id)
            self._undo_stack = [('entry', entry, related_transactions)]
            self.undo_action.setEnabled(True)
            self.undo_action.setText(f"Undo Delete '{entry.label}'")

            self.ledger_manager.delete_entry_by_id(entry.id)
            self.transaction_manager.delete_transactions_by_entry_id(entry.id)
            self.save_and_refresh()

    def add_transaction(self):
        entry = self.get_selected_entry()
        if not entry:
            return

        dialog = TransactionDialog(parent=self)
        if dialog.exec():
            trans_type = "payment" if entry.entry_type == 'debt' else 'repayment'
            self.transaction_manager.add_transaction(
                entry_id=entry.id,
                transaction_type=trans_type,
                **dialog.transaction_data
            )
            self.update_entry_status(entry)
            self.save_and_refresh()

            # Offer to save as template
            reply = QMessageBox.question(self, "Save Template?",
                f"Save this as a recurring template?\n\n"
                f"Label: {dialog.transaction_data['label']}\n"
                f"Amount: ${dialog.transaction_data['amount']:,.2f}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                templates = self.config.get('transaction_templates', [])
                templates.append({
                    'label': dialog.transaction_data['label'],
                    'amount': dialog.transaction_data['amount'],
                })
                self.config['transaction_templates'] = templates
                save_config(self.config)

    def use_transaction_template(self):
        entry = self.get_selected_entry()
        if not entry:
            return

        templates = self.config.get('transaction_templates', [])
        if not templates:
            QMessageBox.information(self, "No Templates", "No saved templates yet. Add a transaction first and choose to save it as a template.")
            return

        # Show template picker
        items = [f"{t['label']} (${t['amount']:,.2f})" for t in templates]
        chosen, ok = QInputDialog.getItem(self, "Select Template", "Choose a template:", items, 0, False)
        if not ok:
            return

        idx = items.index(chosen)
        template = templates[idx]
        trans_type = "payment" if entry.entry_type == 'debt' else 'repayment'
        self.transaction_manager.add_transaction(
            entry_id=entry.id,
            transaction_type=trans_type,
            label=template['label'],
            amount=template['amount'],
        )
        self.update_entry_status(entry)
        self.save_and_refresh()

    def edit_transaction(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 1:
            item = self.ledger_widgets['transaction_list'].currentItem()
        elif tab_index == 2:
            item = self.history_widgets['transaction_list'].currentItem()
        else:
            return
        if not item:
            return

        trans = item.data(Qt.ItemDataRole.UserRole)
        dialog = TransactionDialog(transaction_data={'label': trans.label, 'amount': trans.amount}, parent=self)
        if dialog.exec():
            trans.label = dialog.transaction_data['label']
            trans.amount = dialog.transaction_data['amount']
            entry = self.get_selected_entry()
            if entry:
                self.update_entry_status(entry)
            self.save_and_refresh()

    def delete_transaction(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 1: 
            item = self.ledger_widgets['transaction_list'].currentItem()
        elif tab_index == 2: 
            item = self.history_widgets['transaction_list'].currentItem()
        else:
            return

        if not item:
            return
        
        trans = item.data(Qt.ItemDataRole.UserRole)
        entry = self.get_selected_entry()

        reply = QMessageBox.question(self, "Confirm Delete", f"Delete transaction '{trans.label}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._undo_stack = [('transaction', trans)]
            self.undo_action.setEnabled(True)
            self.undo_action.setText(f"Undo Delete '{trans.label}'")

            self.transaction_manager.delete_transaction_by_id(trans.id)
            if entry:
                self.update_entry_status(entry)
            self.save_and_refresh()

    def add_journal_entry(self):
        notebook = "General"
        if self.notebook_list.currentItem():
            notebook = self.notebook_list.currentItem().text()
        text, ok = QInputDialog.getMultiLineText(self, "New Journal Entry", f"New entry in '{notebook}':")
        if ok and text:
            self.journal_manager.add_entry(text, notebook=notebook)
            self.save_and_refresh()

    def edit_journal_entry(self):
        item = self.journal_list.currentItem()
        if not item:
            return
        entry = item.data(Qt.ItemDataRole.UserRole)
        text, ok = QInputDialog.getMultiLineText(self, "Edit Journal Entry", "Edit your entry:", entry.content)
        if ok and text:
            entry.content = text
            self.save_and_refresh()

    def delete_journal_entry(self):
        item = self.journal_list.currentItem()
        if not item:
            return

        entry = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Confirm Delete", "Delete this journal entry?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._undo_stack = [('journal', entry)]
            self.undo_action.setEnabled(True)
            self.undo_action.setText("Undo Delete Journal Entry")
            self.journal_manager.delete_entry_by_id(entry.id)
            self.save_and_refresh()

    def add_notebook(self):
        name, ok = QInputDialog.getText(self, "New Notebook", "Notebook name:")
        if ok and name and name.strip():
            name = name.strip()
            existing = self.journal_manager.get_notebooks()
            if name in existing:
                QMessageBox.warning(self, "Duplicate", f"A notebook named '{name}' already exists.")
                return
            # Create an empty entry to establish the notebook, then immediately delete it
            # Actually, just add a placeholder - better UX is to just select it and let user add entries
            # We'll create a dummy entry approach won't work. Instead, just add an entry directly.
            # Simplest: create the notebook by adding an entry to it
            text, text_ok = QInputDialog.getMultiLineText(self, "First Entry", f"Add the first entry to '{name}':")
            if text_ok and text:
                self.journal_manager.add_entry(text, notebook=name)
                self.save_and_refresh()
                # Select the new notebook
                for i in range(self.notebook_list.count()):
                    if self.notebook_list.item(i).text() == name:
                        self.notebook_list.setCurrentRow(i)
                        break

    def rename_notebook(self):
        current_item = self.notebook_list.currentItem()
        if not current_item or current_item.text() == "General":
            return
        old_name = current_item.text()
        new_name, ok = QInputDialog.getText(self, "Rename Notebook", "New name:", text=old_name)
        if ok and new_name and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            for entry in self.journal_manager.entries:
                if entry.notebook == old_name:
                    entry.notebook = new_name
            self.save_and_refresh()

    # --- AI-Specific Methods ---

    def run_ai_health_check(self):
        if not self.ai_analyser.api_key:
            QMessageBox.warning(self, "AI Disabled", "Please set your API key first.")
            return
            
        report = self.ai_analyser.generate_insights(
            self.ledger_manager.get_all_entries(),
            self.transaction_manager.get_all_transactions()
        )
        msg_box = QMessageBox(self)
        msg_box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg_box.setWindowTitle("AI Financial Health Check")
        msg_box.setText(report)
        msg_box.exec()

    def run_ai_chat(self):
        if not self.ai_analyser.api_key:
            QMessageBox.warning(self, "AI Disabled", "Please set your API key first.")
            return
            
        dialog = AiChatDialog(self.ai_analyser, self.ledger_manager, self.transaction_manager, self)
        dialog.exec()

    def run_ai_command_bar(self):
        if not self.ai_analyser.api_key:
            QMessageBox.warning(self, "AI Disabled", "Please set your API key first.")
            return
            
        command_str, ok = QInputDialog.getText(self, "AI Command Bar", "Enter a command (e.g., 'add $50 debt for groceries'):")
        if not (ok and command_str):
            return
        
        parsed = self.ai_analyser.parse_command_to_json(command_str)
        commands = parsed.get("commands", [])
        if not commands:
            QMessageBox.warning(self, "AI Command Error", "Sorry, I couldn't understand that command.")
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm AI Plan")
        msg_box.setText("The AI understood the following plan. Proceed?")
        plan_text = "\n".join([f"Step {i+1}: {c.get('action','?').replace('_',' ').title()} with details: {c.get('payload',{})}" for i, c in enumerate(commands)])
        msg_box.setInformativeText(plan_text)
        yes_btn = msg_box.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        edit_btn = msg_box.addButton("Edit Plan...", QMessageBox.ButtonRole.ActionRole)
        msg_box.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            self.execute_ai_plan(commands)
        elif msg_box.clickedButton() == edit_btn:
            editor = AiPlanEditorDialog(commands, self.tag_manager, self)
            if editor.exec():
                self.execute_ai_plan(editor.commands)
            
    def execute_ai_plan(self, commands):
        for i, command in enumerate(commands):
            if command['action'] == 'add_entry' and not command['payload'].get('label'):
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("Incomplete AI Plan")
                msg_box.setText(f"The AI plan is incomplete. Step {i+1} is missing a required 'label'.")
                msg_box.setInformativeText("Would you like to edit the plan to add the missing information?")
                edit_btn = msg_box.addButton("Edit Plan", QMessageBox.ButtonRole.ActionRole)
                msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                msg_box.exec()

                if msg_box.clickedButton() == edit_btn:
                    editor = AiPlanEditorDialog(commands, self.tag_manager, self)
                    if editor.exec():
                        self.execute_ai_plan(editor.commands)
                return

        for command in commands:
            try:
                if command['action'] == 'add_entry':
                    self.ledger_manager.add_entry(**command['payload'])
                elif command['action'] == 'add_transaction':
                    payload = command['payload']
                    target_label = payload.get('target_entry_label', '').lower()
                    if not target_label:
                        raise ValueError("AI command 'add_transaction' is missing 'target_entry_label'.")
                    
                    target_entry = next((e for e in self.ledger_manager.get_all_entries() if target_label in e.label.lower()), None)
                    
                    if target_entry:
                        trans_data = {
                            'entry_id': target_entry.id,
                            'transaction_type': payload.get('transaction_type', 'payment'),
                            'label': payload.get('label', 'AI Transaction'),
                            'amount': payload.get('amount', 0)
                        }
                        self.transaction_manager.add_transaction(**trans_data)
                        self.update_entry_status(target_entry)
                    else:
                        raise ValueError(f"Could not find an entry matching '{payload.get('target_entry_label')}'.")
            except Exception as e:
                QMessageBox.critical(self, "Execution Error", f"Failed to execute AI plan.\nCommand: {command}\nError: {e}")
                return

        self.save_and_refresh()
        QMessageBox.information(self, "AI Command Executed", "The AI commands were executed successfully.")

    # --- Tool Actions ---
    
    def show_monthly_summary(self):
        """Shows a monthly breakdown of payments made."""
        all_transactions = self.transaction_manager.get_all_transactions()
        if not all_transactions:
            QMessageBox.information(self, "Monthly Summary", "No transactions recorded yet.")
            return

        # Group by month
        monthly = {}
        for t in all_transactions:
            key = t.date_paid.strftime("%Y-%m")
            if key not in monthly:
                monthly[key] = {'payments': 0.0, 'repayments': 0.0, 'count': 0}
            monthly[key]['count'] += 1
            if t.transaction_type == 'payment':
                monthly[key]['payments'] += t.amount
            else:
                monthly[key]['repayments'] += t.amount

        # Build report
        lines = ["<h3>Monthly Payment Summary</h3><table style='width:100%'>"]
        lines.append("<tr><th style='text-align:left'>Month</th><th style='text-align:right'>Payments</th>"
                     "<th style='text-align:right'>Repayments</th><th style='text-align:right'>Total</th>"
                     "<th style='text-align:right'>#</th></tr>")

        for month in sorted(monthly.keys(), reverse=True):
            data = monthly[month]
            total = data['payments'] + data['repayments']
            lines.append(
                f"<tr><td>{month}</td>"
                f"<td style='text-align:right; color:#bf616a'>${data['payments']:,.2f}</td>"
                f"<td style='text-align:right; color:#a3be8c'>${data['repayments']:,.2f}</td>"
                f"<td style='text-align:right'><b>${total:,.2f}</b></td>"
                f"<td style='text-align:right'>{data['count']}</td></tr>"
            )
        lines.append("</table>")

        msg = QMessageBox(self)
        msg.setWindowTitle("Monthly Payment Summary")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText("\n".join(lines))
        msg.setMinimumWidth(500)
        msg.exec()

    def quick_add_payment(self):
        """Quick-add a payment from the dashboard dropdown."""
        if self.quick_add_combo.currentIndex() < 0:
            return
        entry = self.quick_add_combo.currentData()
        if not entry:
            return

        dialog = TransactionDialog(parent=self)
        if dialog.exec():
            trans_type = "payment" if entry.entry_type == 'debt' else 'repayment'
            self.transaction_manager.add_transaction(
                entry_id=entry.id,
                transaction_type=trans_type,
                **dialog.transaction_data
            )
            self.update_entry_status(entry)
            self.save_and_refresh()

    def show_debt_snowball(self):
        active_debts = [e for e in self.ledger_manager.get_all_entries() if e.entry_type == 'debt' and e.status == 'active']
        if not active_debts:
            QMessageBox.information(self, "Debt Strategy", "Congratulations! You have no active debts.")
            return
            
        priority_debt = suggest_snowball_priority(active_debts, self.transaction_manager.get_all_transactions())
        if priority_debt:
            balance = calculate_balance_for_entry(priority_debt, self.transaction_manager.get_all_transactions())
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Debt Payoff Strategy")
            msg_box.setTextFormat(Qt.TextFormat.RichText)
            msg_box.setText(f"Using the Snowball method, your priority should be:<br><br><b>{priority_debt.label}</b><br>Remaining Balance: ${balance:,.2f}")
            msg_box.exec()
        else:
            QMessageBox.information(self, "Debt Strategy", "Congratulations! All your active debts have a zero or negative balance.")

    def show_what_if_calc(self):
        dialog = WhatIfDialog(self)
        if dialog.exec():
            eta_string = calculate_what_if_eta(self.ledger_manager.get_all_entries(), self.transaction_manager.get_all_transactions(), dialog.amount)
            QMessageBox.information(self, "What-If Result", eta_string)

    def log_net_position(self):
        """Manually log a net position snapshot (also happens automatically on save)."""
        self._record_net_position_snapshot()
        net_pos = self.net_worth_manager.get_all_snapshots()[0].net_position
        QMessageBox.information(self, "Snapshot Logged", f"Net position snapshot logged: ${net_pos:,.2f}")
        self.save_and_refresh()

    def _record_net_position_snapshot(self):
        """Auto-records a net position snapshot if it has changed since the last one."""
        all_e = self.ledger_manager.get_all_entries()
        all_t = self.transaction_manager.get_all_transactions()
        debt_bal = sum(calculate_balance_for_entry(e, all_t) for e in all_e if e.entry_type == 'debt')
        loan_bal = sum(calculate_balance_for_entry(e, all_t) for e in all_e if e.entry_type == 'loan')
        net_pos = loan_bal - debt_bal

        # Only record if the value has changed since the last snapshot
        snapshots = self.net_worth_manager.get_all_snapshots()
        if snapshots and abs(snapshots[0].net_position - net_pos) < 0.01:
            return
        self.net_worth_manager.add_snapshot(net_pos)

    # --- Helper & Utility Methods ---

    def update_entry_status(self, entry: LedgerEntry):
        """Updates an entry's status based on its balance. Shows celebration on payoff."""
        balance = calculate_balance_for_entry(entry, self.transaction_manager.get_all_transactions())
        if balance <= 0 and entry.status == 'active':
            entry.status = 'paid'
            entry_type = "debt" if entry.entry_type == 'debt' else "loan"
            msg = QMessageBox(self)
            msg.setWindowTitle("Fully Paid Off!")
            msg.setTextFormat(Qt.TextFormat.RichText)
            msg.setText(
                f"<h2>Congratulations!</h2>"
                f"<p><b>{entry.label}</b> (${entry.amount:,.2f}) has been fully settled!</p>"
                f"<p>This {entry_type} has been moved to your <b>History</b> tab.</p>"
            )
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
        elif balance > 0 and entry.status == 'paid':
            entry.status = 'active'
    
    def save_and_refresh(self):
        """Saves all data to disk, auto-logs net position, refreshes the UI."""
        self._record_net_position_snapshot()
        self.storage_manager.save_data(self.ledger_manager, self.transaction_manager, self.journal_manager, self.net_worth_manager)
        self.refresh_ui()
        self.statusBar().showMessage("Data Saved!", 2000)

    def get_selected_entry(self):
        """Gets the selected entry object from the currently active tab."""
        tab_index = self.tabs.currentIndex()
        if tab_index == 1: # Ledger Tab
            item = self.active_list_widget.currentItem()
            return item.data(Qt.ItemDataRole.UserRole) if item else None
        elif tab_index == 2: # History Tab
            item = self.history_list_widget.currentItem()
            return item.data(Qt.ItemDataRole.UserRole) if item else None
        return None

    def get_selected_entry_id(self):
        if not hasattr(self, 'active_list_widget'):
            return None
        entry = self.get_selected_entry()
        return entry.id if entry else None

    def get_selected_journal_id(self):
        if not hasattr(self, 'journal_list'):
            return None
        item = self.journal_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole).id if item else None

    def undo_last_delete(self):
        if not self._undo_stack:
            return
        undo_item = self._undo_stack.pop()
        undo_type = undo_item[0]

        if undo_type == 'entry':
            entry = undo_item[1]
            transactions = undo_item[2]
            self.ledger_manager.entries.append(entry)
            self.transaction_manager.transactions.extend(transactions)
            self.statusBar().showMessage(f"Restored '{entry.label}' and {len(transactions)} transaction(s)", 3000)
        elif undo_type == 'transaction':
            trans = undo_item[1]
            self.transaction_manager.transactions.append(trans)
            # Re-check parent entry status
            parent = self.ledger_manager.get_entry_by_id(trans.entry_id)
            if parent:
                self.update_entry_status(parent)
            self.statusBar().showMessage(f"Restored transaction '{trans.label}'", 3000)
        elif undo_type == 'journal':
            journal_entry = undo_item[1]
            self.journal_manager.entries.append(journal_entry)
            self.statusBar().showMessage("Restored journal entry", 3000)

        self.undo_action.setEnabled(bool(self._undo_stack))
        self.undo_action.setText("Undo Last Delete")
        self.save_and_refresh()

    def clear_all_data(self):
        reply = QMessageBox.critical(self, "Confirm Clear All Data",
                                     "WARNING: This will permanently delete ALL data. This action cannot be undone. Are you absolutely sure?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                                     QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
            self.ledger_manager.entries.clear()
            self.transaction_manager.transactions.clear()
            self.journal_manager.entries.clear()
            self.net_worth_manager.snapshots.clear()
            self.save_and_refresh()

    def export_all_data(self):
        path = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if path:
            try:
                export_data_to_csv(self.ledger_manager, self.transaction_manager, path)
                QMessageBox.information(self, "Export Successful", f"Data successfully exported to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"An error occurred: {e}")

    def backup_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Backup", "finance_board_backup.json", "JSON Files (*.json)")
        if path:
            if self.storage_manager.create_manual_backup(path):
                QMessageBox.information(self, "Backup Successful", f"Data backed up to:\n{path}")
            else:
                QMessageBox.critical(self, "Backup Failed", "Could not create the backup file.")

    def restore_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore from Backup", "", "JSON Files (*.json)")
        if not path:
            return
        reply = QMessageBox.warning(self, "Confirm Restore",
                                    "This will replace ALL current data with the backup.\n"
                                    "Your current data will be auto-backed up first.\n\nContinue?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self.storage_manager.restore_from_backup(path):
            # Reload all data from the restored file
            all_data = self.storage_manager.load_data()
            from Backend.core.ledger_manager import LedgerEntry
            from Backend.core.transaction_manager import Transaction
            from Backend.core.journal_manager import JournalEntry
            from Backend.core.net_worth_manager import NetWorthSnapshot
            self.ledger_manager.entries = [LedgerEntry.from_dict(d) for d in all_data.get("ledger_entries", [])]
            self.transaction_manager.transactions = [Transaction.from_dict(t) for t in all_data.get("transactions", [])]
            self.journal_manager.entries = [JournalEntry.from_dict(j) for j in all_data.get("journal_entries", [])]
            self.net_worth_manager.snapshots = [NetWorthSnapshot.from_dict(n) for n in all_data.get("net_worth_snapshots", [])]
            self.refresh_ui()
            QMessageBox.information(self, "Restore Successful", "Data has been restored from the backup.")
        else:
            QMessageBox.critical(self, "Restore Failed", "The selected file is not a valid Finance Board backup.")

    def show_api_key_dialog(self, is_first_run=False):
        current_key = self.config.get("OPENROUTER_API_KEY", "")
        dialog = ApiKeyDialog(current_key=current_key, parent=self)
        if dialog.exec():
            self.config["OPENROUTER_API_KEY"] = dialog.api_key
            save_config(self.config)
            self.ai_analyser.api_key = dialog.api_key
            QMessageBox.information(self, "Success", "API Key saved!")
        elif is_first_run:
            QMessageBox.warning(self, "AI Disabled", "No API key provided.")

    def closeEvent(self, event):
        """Ensures data is saved when the application is closed."""
        self.save_and_refresh()
        super().closeEvent(event)