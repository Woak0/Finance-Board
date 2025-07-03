from PyQt6.QtWidgets import *
from PyQt6.QtGui import QAction, QFont, QKeySequence, QIcon
from PyQt6.QtCore import Qt
import copy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

# Import all necessary backend components
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

# --- DIALOGS (Unchanged) ---
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
        
        # Dialog buttons
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
        QApplication.processEvents() # Allow UI to update
        
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
                # Preserve keys the dialog doesn't know about (e.g., target_entry_label)
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
        
        # Assign all manager instances to the main window
        for name, instance in managers.items():
            setattr(self, name, instance)

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
        
        self.tabs.currentChanged.connect(self.refresh_ui)
        self.refresh_ui()

    # --- UI Creation Methods ---

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        s = self.style()
        
        # File Menu
        file_menu = menu_bar.addMenu("File")
        save_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)), "Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_and_refresh)
        export_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ArrowUp)), "Export All to CSV", self)
        export_action.triggered.connect(self.export_all_data)
        api_key_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)), "Set API Key...", self)
        api_key_action.triggered.connect(self.show_api_key_dialog)
        clear_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)), "Clear All Data...", self)
        clear_action.triggered.connect(self.clear_all_data)
        file_menu.addAction(save_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(api_key_action)
        file_menu.addSeparator()
        file_menu.addAction(clear_action)

        # Tools Menu
        tools_menu = menu_bar.addMenu("Tools")
        snowball_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward)), "Debt Payoff Strategy", self)
        snowball_action.triggered.connect(self.show_debt_snowball)
        whatif_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)), "What-If Calculator", self)
        whatif_action.triggered.connect(self.show_what_if_calc)
        networth_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ToolBarVerticalExtensionButton)), "Log Net Worth Snapshot", self)
        networth_action.triggered.connect(self.log_net_worth)
        tools_menu.addAction(snowball_action)
        tools_menu.addAction(whatif_action)
        tools_menu.addAction(networth_action)

        # AI Tools Menu
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
        self.tabs.addTab(self.create_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self.create_ledger_tab(), "Ledger & Transactions")
        self.tabs.addTab(self.create_history_tab(), "History")
        self.tabs.addTab(self.create_journal_tab(), "Journal")

    def create_dashboard_tab(self):
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        title = QLabel("Finance Board Dashboard")
        title.setObjectName("Header")
        main_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)

        grid_layout = QGridLayout()
        main_layout.addLayout(grid_layout)

        # Summary Panel
        summary_container = QWidget()
        summary_layout = QFormLayout(summary_container)
        self.summary_labels = {
            'debt_incurred': QLabel(), 'debt_paid': QLabel(), 'debt_remaining': QLabel(), 'debt_eta': QLabel(),
            'loan_out': QLabel(), 'loan_repaid': QLabel(), 'loan_remaining': QLabel(), 'net_position': QLabel()
        }
        for label in self.summary_labels.values():
            label.setFont(QFont("Segoe UI", 11))
        self.summary_labels['net_position'].setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        summary_layout.addRow(QLabel()) # Spacer
        summary_layout.addRow(QLabel("<b>DEBTS (Money You Owe)</b>"))
        summary_layout.addRow("Total Debt Incurred:", self.summary_labels['debt_incurred'])
        summary_layout.addRow("Total Payments Made:", self.summary_labels['debt_paid'])
        summary_layout.addRow("<b>Remaining Debt Balance:</b>", self.summary_labels['debt_remaining'])
        summary_layout.addRow("<i>Est. Debt-Free Date:</i>", self.summary_labels['debt_eta'])
        summary_layout.addRow(QLabel()) # Spacer
        summary_layout.addRow(QLabel("<b>LOANS (Money Owed to You)</b>"))
        summary_layout.addRow("Total Loaned Out:", self.summary_labels['loan_out'])
        summary_layout.addRow("Total Repaid to You:", self.summary_labels['loan_repaid'])
        summary_layout.addRow("<b>Remaining to Collect:</b>", self.summary_labels['loan_remaining'])
        summary_layout.addRow(QLabel()) # Spacer
        summary_layout.addRow(QLabel("---"))
        summary_layout.addRow("<h2>Net Financial Position:</h2>", self.summary_labels['net_position'])

        # Chart Canvases
        self.pie_chart_canvas = self.create_pie_chart()
        self.bar_chart_canvas = self.create_bar_chart()
        self.line_chart_canvas = self.create_line_chart()

        # Add widgets to grid
        grid_layout.addWidget(summary_container, 0, 0)
        grid_layout.addWidget(self.pie_chart_canvas, 0, 1)
        grid_layout.addWidget(self.bar_chart_canvas, 0, 2)
        grid_layout.addWidget(self.line_chart_canvas, 1, 0, 1, 3) # Span across all 3 columns
        grid_layout.setColumnStretch(0, 2)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        return widget
    
    def create_pie_chart(self):
        fig, self.pie_ax = plt.subplots(facecolor='#2e3440')
        self.pie_ax.set_facecolor('#2e3440')
        plt.subplots_adjust(left=0.1, right=0.75, top=0.9, bottom=0.1)
        return FigureCanvas(fig)

    def create_bar_chart(self):
        fig, self.bar_ax = plt.subplots(facecolor='#2e3440')
        self.bar_ax.set_facecolor('#2e3440')
        plt.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.25)
        return FigureCanvas(fig)

    def create_line_chart(self):
        fig, self.line_ax = plt.subplots(facecolor='#2e3440')
        self.line_ax.set_facecolor('#2e3440')
        plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.2)
        return FigureCanvas(fig)

    def _create_details_panel_widgets(self):
        """Factory method to create a reusable details panel."""
        s = self.style()
        container = QWidget()
        layout = QVBoxLayout(container)
        widgets = {}

        # Top info labels
        widgets['detail_label'] = QLabel("No item selected")
        widgets['detail_label'].setObjectName("SubHeader")
        widgets['detail_balance'] = QLabel()
        widgets['detail_info'] = QLabel()
        widgets['detail_info'].setWordWrap(True)
        widgets['detail_info'].setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(widgets['detail_label'])
        layout.addWidget(widgets['detail_balance'])
        layout.addWidget(widgets['detail_info'])

        # Transactions header with delete button
        trans_header_layout = QHBoxLayout()
        trans_label = QLabel("Transactions")
        trans_label.setStyleSheet("font-size: 12pt; margin-top: 15px;")
        widgets['delete_transaction_btn'] = QPushButton(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)), "")
        widgets['delete_transaction_btn'].setToolTip("Delete Selected Transaction")
        widgets['delete_transaction_btn'].setEnabled(False)
        widgets['delete_transaction_btn'].clicked.connect(self.delete_transaction)
        trans_header_layout.addWidget(trans_label)
        trans_header_layout.addStretch()
        trans_header_layout.addWidget(widgets['delete_transaction_btn'])
        layout.addLayout(trans_header_layout)

        # Transactions list
        widgets['transaction_list'] = QListWidget()
        widgets['transaction_list'].currentItemChanged.connect(self.on_transaction_selection_changed)
        layout.addWidget(widgets['transaction_list'], 1)

        # Bottom buttons
        widgets['add_payment_btn'] = QPushButton("Add Payment")
        widgets['add_payment_btn'].setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)))
        widgets['add_payment_btn'].clicked.connect(self.add_transaction)
        layout.addWidget(widgets['add_payment_btn'])

        crud_layout = QHBoxLayout()
        add_btn = QPushButton("Add Entry")
        add_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileIcon)))
        add_btn.clicked.connect(self.add_entry)
        edit_btn = QPushButton("Edit Entry")
        edit_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)))
        edit_btn.clicked.connect(self.edit_entry)
        delete_btn = QPushButton("Delete Entry")
        delete_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)))
        delete_btn.clicked.connect(self.delete_entry)
        
        crud_layout.addStretch()
        crud_layout.addWidget(add_btn)
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
        # Paid items cannot have new payments added.
        self.history_widgets['add_payment_btn'].setVisible(False)

        layout.addWidget(list_container, 1)
        layout.addWidget(self.history_details_panel, 2)
        return widget

    def create_journal_tab(self):
        s = self.style()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        title = QLabel("Financial Journal")
        title.setObjectName("Header")
        layout.addWidget(title)
        
        self.journal_list = QListWidget()
        self.journal_list.setWordWrap(True)
        self.journal_list.currentItemChanged.connect(self.on_journal_selection_changed)
        layout.addWidget(self.journal_list, 1)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Entry")
        add_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon)))
        add_btn.clicked.connect(self.add_journal_entry)
        self.delete_journal_btn = QPushButton("Delete Selected Entry")
        self.delete_journal_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)))
        self.delete_journal_btn.clicked.connect(self.delete_journal_entry)
        self.delete_journal_btn.setEnabled(False)
        
        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(self.delete_journal_btn)
        layout.addLayout(btn_layout)
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
        
        # Update summary labels
        self.summary_labels['debt_incurred'].setText(f"${total_debt:,.2f}")
        self.summary_labels['debt_paid'].setText(f"${total_paid:,.2f}")
        self.summary_labels['debt_remaining'].setText(f"${debt_balance:,.2f}")
        self.summary_labels['debt_eta'].setText(calculate_overall_eta(debt_entries, [t for t in all_transactions if t.transaction_type == 'payment']))
        self.summary_labels['loan_out'].setText(f"${total_loaned:,.2f}")
        self.summary_labels['loan_repaid'].setText(f"${total_repaid:,.2f}")
        self.summary_labels['loan_remaining'].setText(f"${loan_balance:,.2f}")
        self.summary_labels['net_position'].setText(f"${net_position:,.2f}")

        # Update pie chart
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
        
        # Update bar chart
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
        self.bar_ax.set_ylabel('Amount ($)', color='white')
        self.bar_ax.set_xticks(x, categories)
        self.bar_ax.legend(labelcolor='white', facecolor='#3b4252', edgecolor='#4c566a', bbox_to_anchor=(0.5, -0.1), loc='upper center')
        self.bar_chart_canvas.draw()
        
        # Update line chart
        self.line_ax.clear()
        self.line_ax.set_title('Net Worth Over Time', color='white')
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
            self.line_ax.text(0.5, 0.5, 'Log at least two snapshots to see a trend', ha='center', va='center', color='gray')
        self.line_chart_canvas.draw()

    def refresh_ledger_list(self):
        current_id = self.get_selected_entry_id()
        self.active_list_widget.clear()
        selected_item_to_restore = None
        
        # Use 'or' to provide a default empty string if label is None, preventing sort errors
        sorted_entries = sorted(self.ledger_manager.get_all_entries(), key=lambda e: e.label or '')
        
        for entry in sorted_entries:
            if entry.status == 'active':
                item = QListWidgetItem(f"{entry.label}")
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

        for entry in sorted_entries:
            if entry.status == 'paid':
                item = QListWidgetItem(f"{entry.label}")
                item.setData(Qt.ItemDataRole.UserRole, entry)
                self.history_list_widget.addItem(item)
                if entry and current_id and entry.id == current_id:
                    selected_item_to_restore = item

        if selected_item_to_restore:
            self.history_list_widget.setCurrentItem(selected_item_to_restore)
        else:
            self._update_details_panel(None, self.history_widgets)

    def refresh_journal_list(self):
        current_id = self.get_selected_journal_id()
        self.journal_list.clear()
        if not self.journal_manager.get_all_entries():
            self.delete_journal_btn.setEnabled(False)
            return
            
        for entry in self.journal_manager.get_all_entries():
            item = QListWidgetItem(f"{entry.date_created.strftime('%Y-%m-%d %H:%M')}\n{entry.content}")
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.journal_list.addItem(item)
            if entry and current_id and entry.id == current_id:
                self.journal_list.setCurrentItem(item)

    def _update_details_panel(self, entry, widgets):
        """A generic function to update a details panel, given an entry and a dict of widgets."""
        widgets['transaction_list'].clear()
        widgets['delete_transaction_btn'].setEnabled(False)

        if entry:
            # Enable the 'Add Payment' button only if the entry is active
            widgets['add_payment_btn'].setEnabled(entry.status == 'active')
            widgets['add_payment_btn'].setText(f"Add {'Payment' if entry.entry_type == 'debt' else 'Repayment'}")
            
            balance = calculate_balance_for_entry(entry, self.transaction_manager.get_all_transactions())
            widgets['detail_label'].setText(entry.label)
            widgets['detail_balance'].setText(f"<b>Current Balance: ${balance:,.2f}</b>")
            widgets['detail_info'].setText(
                f"<b>Type:</b> {entry.entry_type.capitalize()}<br>"
                f"<b>Status:</b> {entry.status.capitalize()}<br>"
                f"<b>Tags:</b> {', '.join(entry.tags) if entry.tags else 'None'}<br>"
                f"<b>Comments:</b> {entry.comments or 'None'}"
            )
            
            transactions = self.transaction_manager.get_transactions_for_entry(entry.id)
            for t in sorted(transactions, key=lambda t: t.date_paid, reverse=True):
                item = QListWidgetItem(f"{t.date_paid.strftime('%Y-%m-%d')} - {t.label} (${t.amount:,.2f})")
                item.setData(Qt.ItemDataRole.UserRole, t)
                widgets['transaction_list'].addItem(item)
        else:
            # Reset the panel if no entry is selected
            widgets['detail_label'].setText("No item selected")
            widgets['detail_balance'].setText("")
            widgets['detail_info'].setText("")
            widgets['add_payment_btn'].setEnabled(False)

    # --- Event Handlers / Slots ---

    def on_active_list_selection(self, current, previous):
        entry = current.data(Qt.ItemDataRole.UserRole) if current else None
        self._update_details_panel(entry, self.ledger_widgets)

    def on_history_list_selection(self, current, previous):
        entry = current.data(Qt.ItemDataRole.UserRole) if current else None
        self._update_details_panel(entry, self.history_widgets)

    def on_journal_selection_changed(self):
        self.delete_journal_btn.setEnabled(bool(self.journal_list.currentItem()))
    
    def on_transaction_selection_changed(self):
        """Enables the delete button for the correct tab's transaction list."""
        tab_index = self.tabs.currentIndex()
        if tab_index == 1: # Ledger Tab
            is_selected = bool(self.ledger_widgets['transaction_list'].currentItem())
            self.ledger_widgets['delete_transaction_btn'].setEnabled(is_selected)
        elif tab_index == 2: # History Tab
            is_selected = bool(self.history_widgets['transaction_list'].currentItem())
            self.history_widgets['delete_transaction_btn'].setEnabled(is_selected)

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
            
    def delete_entry(self):
        entry = self.get_selected_entry()
        if not entry:
            QMessageBox.warning(self, "No Selection", "Please select an entry to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", f"Delete '{entry.label}' and all its transactions?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
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

    def delete_transaction(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 1: # Ledger Tab
            item = self.ledger_widgets['transaction_list'].currentItem()
        elif tab_index == 2: # History Tab
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
            self.transaction_manager.delete_transaction_by_id(trans.id)
            if entry:
                # This will automatically move an item from "paid" to "active" if necessary
                self.update_entry_status(entry)
            self.save_and_refresh()

    def add_journal_entry(self):
        text, ok = QInputDialog.getMultiLineText(self, "New Journal Entry", "Enter your thoughts or notes:")
        if ok and text:
            self.journal_manager.add_entry(text)
            self.save_and_refresh()

    def delete_journal_entry(self):
        item = self.journal_list.currentItem()
        if not item:
            return

        entry = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Confirm Delete", "Delete this journal entry?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.journal_manager.delete_entry_by_id(entry.id)
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
        
        # Confirmation dialog
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
        # First, validate the entire plan before executing any part of it.
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
                        self.execute_ai_plan(editor.commands) # Recursively call with the new plan
                return # Stop execution of the faulty plan

        # If validation passes, execute the plan.
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

    def log_net_worth(self):
        all_e = self.ledger_manager.get_all_entries()
        all_t = self.transaction_manager.get_all_transactions()
        debt_bal = sum(calculate_balance_for_entry(e, all_t) for e in all_e if e.entry_type == 'debt')
        loan_bal = sum(calculate_balance_for_entry(e, all_t) for e in all_e if e.entry_type == 'loan')
        net_pos = loan_bal - debt_bal
        self.net_worth_manager.add_snapshot(net_pos)
        QMessageBox.information(self, "Net Worth Logged", f"Successfully logged a new net worth snapshot of ${net_pos:,.2f}.")
        self.save_and_refresh()

    # --- Helper & Utility Methods ---

    def update_entry_status(self, entry: LedgerEntry):
        """Updates an entry's status based on its balance."""
        balance = calculate_balance_for_entry(entry, self.transaction_manager.get_all_transactions())
        if balance <= 0 and entry.status == 'active':
            entry.status = 'paid'
        elif balance > 0 and entry.status == 'paid':
            entry.status = 'active'
    
    def save_and_refresh(self):
        """Saves all data to disk, refreshes the UI, and shows a status message."""
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