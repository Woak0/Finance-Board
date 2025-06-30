from PyQt6.QtWidgets import *
from PyQt6.QtGui import QAction, QFont, QKeySequence, QIcon
from PyQt6.QtCore import Qt
import copy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from Backend.core.ledger_manager import LedgerManager, LedgerEntry
from Backend.core.transaction_manager import TransactionManager
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
    def __init__(self, current_key="", parent=None):
        super().__init__(parent);self.setWindowTitle("AI Feature Setup");self.setMinimumWidth(400);self.api_key=None;layout=QVBoxLayout(self);info_label=QLabel("To enable AI features, a free API key from OpenRouter.ai is required...");info_label.setWordWrap(True);link_label=QLabel('<a href="https://openrouter.ai/keys" style="color:#88c0d0;">Open OpenRouter.ai Keys Page</a>');link_label.setOpenExternalLinks(True);self.key_input=QLineEdit();self.key_input.setText(current_key);self.key_input.setPlaceholderText("Paste your API key here (e.g., sk-or-...)");button_box=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);button_box.accepted.connect(self.accept);button_box.rejected.connect(self.reject);layout.addWidget(info_label);layout.addWidget(link_label);layout.addWidget(self.key_input);layout.addWidget(button_box)
    def accept(self):
        key=self.key_input.text().strip();
        if key.startswith("sk-or-"):self.api_key=key;super().accept()
        else:QMessageBox.warning(self,"Invalid Key","Please enter a valid OpenRouter API key.")

class EntryDialog(QDialog):
    def __init__(self,tag_manager,entry=None,parent=None):
        super().__init__(parent);self.setWindowTitle("Add/Edit Entry");self.entry_data={};layout=QVBoxLayout(self);form_layout=QFormLayout();self.label_input=QLineEdit(entry.label if entry else"");self.amount_input=QDoubleSpinBox();self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.PlusMinus);self.amount_input.setSingleStep(10);self.amount_input.setRange(0.01,1e9);self.amount_input.setDecimals(2);self.amount_input.setValue(entry.amount if entry else 100.0);self.type_input=QComboBox();self.type_input.addItems(["debt","loan"]);
        if entry:self.type_input.setCurrentText(entry.entry_type)
        self.comments_input=QLineEdit(entry.comments if entry else"");form_layout.addRow("Label:",self.label_input);form_layout.addRow("Amount:",self.amount_input);form_layout.addRow("Type:",self.type_input);form_layout.addRow("Comments:",self.comments_input);layout.addLayout(form_layout);tags_label=QLabel("Tags");tags_label.setStyleSheet("font-weight:bold;margin-top:10px;");layout.addWidget(tags_label);self.tags_list_widget=QListWidget();self.tags_list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection);layout.addWidget(self.tags_list_widget);all_tags=tag_manager.get_standard_tags();selected_tags=set(entry.tags if entry else[]);
        for tag in all_tags:item=QListWidgetItem(tag);self.tags_list_widget.addItem(item);
        if tag in selected_tags:item.setSelected(True)
        for tag in selected_tags:
            if tag.startswith("other:"):self.tags_list_widget.addItem(tag);self.tags_list_widget.findItems(tag,Qt.MatchFlag.MatchExactly)[0].setSelected(True)
        self.button_box=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);self.button_box.accepted.connect(self.accept);self.button_box.rejected.connect(self.reject);layout.addWidget(self.button_box)
    def accept(self):
        if not self.label_input.text().strip():QMessageBox.warning(self,"Validation Error","Label cannot be empty.");return
        final_tags=[];selected_items=self.tags_list_widget.selectedItems()
        for item in selected_items:
            tag_text=item.text()
            if tag_text=="Other (Specify Custom)":
                custom_text,ok=QInputDialog.getText(self,"Custom Tag","Enter your custom tag name:")
                if ok and custom_text.strip():final_tags.append(f"other:{custom_text.strip()}")
            elif not tag_text.startswith("other:"):final_tags.append(tag_text)
        self.entry_data={'label':self.label_input.text().strip(),'amount':self.amount_input.value(),'entry_type':self.type_input.currentText(),'comments':self.comments_input.text().strip()or None,'tags':list(set(final_tags))};super().accept()

class TransactionDialog(QDialog):
    def __init__(self,parent=None):super().__init__(parent);self.setWindowTitle("Add Transaction");self.transaction_data={};form_layout=QFormLayout(self);self.label_input=QLineEdit();self.amount_input=QDoubleSpinBox();self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.PlusMinus);self.amount_input.setSingleStep(10);self.amount_input.setRange(0.01,1e9);self.amount_input.setDecimals(2);self.amount_input.setValue(50.0);form_layout.addRow("Label:",self.label_input);form_layout.addRow("Amount:",self.amount_input);self.button_box=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);self.button_box.accepted.connect(self.accept);self.button_box.rejected.connect(self.reject);form_layout.addRow(self.button_box)
    def accept(self):
        if not self.label_input.text().strip():QMessageBox.warning(self,"Validation Error","Label cannot be empty.");return
        self.transaction_data={'label':self.label_input.text().strip(),'amount':self.amount_input.value()};super().accept()

class AiChatDialog(QDialog):
    def __init__(self,ai_analyser,ledger_manager,transaction_manager,parent=None):super().__init__(parent);self.ai_analyser=ai_analyser;self.ledger_manager=ledger_manager;self.transaction_manager=transaction_manager;self.setWindowTitle("AI Financial Chat");self.setMinimumSize(600,500);layout=QVBoxLayout(self);self.history=QTextBrowser();self.history.setOpenExternalLinks(True);layout.addWidget(self.history);input_layout=QHBoxLayout();self.input_line=QLineEdit();self.input_line.setPlaceholderText("Ask a question...");self.input_line.returnPressed.connect(self.send_message);send_btn=QPushButton("Send");send_btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight)));send_btn.clicked.connect(self.send_message);input_layout.addWidget(self.input_line);input_layout.addWidget(send_btn);layout.addLayout(input_layout);self.add_message("AI","Hello! How can I help you analyze your finances today?")
    def add_message(self,author,text):self.history.append(f"<b>{author}:</b> {text.replace(chr(10),'<br>')}<br>")
    def send_message(self):
        question=self.input_line.text().strip()
        if not question:return
        self.add_message("You",question);self.input_line.clear();QApplication.processEvents();response=self.ai_analyser.answer_user_question(question,self.ledger_manager.get_all_entries(),self.transaction_manager.get_all_transactions());self.add_message("AI",response);self.history.verticalScrollBar().setValue(self.history.verticalScrollBar().maximum())
class AiPlanEditorDialog(QDialog):
    def __init__(self,commands,tag_manager,parent=None):super().__init__(parent);self.setWindowTitle("Edit AI Plan");self.setMinimumSize(500,400);self.tag_manager=tag_manager;self.commands=copy.deepcopy(commands);layout=QVBoxLayout(self);self.command_list=QListWidget();self.refresh_list();layout.addWidget(self.command_list);btn_layout=QHBoxLayout();edit_btn=QPushButton("Edit Selected");edit_btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)));remove_btn=QPushButton("Remove Selected");remove_btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogDiscardButton)));edit_btn.clicked.connect(self.edit_selected_command);remove_btn.clicked.connect(self.remove_selected_command);btn_layout.addWidget(edit_btn);btn_layout.addWidget(remove_btn);layout.addLayout(btn_layout);self.button_box=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Execute Plan");self.button_box.accepted.connect(self.accept);self.button_box.rejected.connect(self.reject);layout.addWidget(self.button_box)
    def refresh_list(self):self.command_list.clear();[self.command_list.addItem(f"{cmd.get('action','?').replace('_',' ').title()}: {cmd.get('payload',{})}")for cmd in self.commands]
    def edit_selected_command(self):
        item=self.command_list.currentItem();
        if not item:return
        row=self.command_list.row(item);cmd=self.commands[row]
        if cmd['action']=='add_entry':temp_entry=LedgerEntry(label=cmd['payload'].get('label',''),amount=cmd['payload'].get('amount',0),entry_type=cmd['payload'].get('entry_type','debt'));dialog=EntryDialog(self.tag_manager,entry=temp_entry,parent=self);
        if dialog.exec():self.commands[row]['payload']=dialog.entry_data
        self.refresh_list()
    def remove_selected_command(self):
        if not self.command_list.currentItem():return
        if QMessageBox.question(self,"Confirm Remove","Remove this step from the plan?")==QMessageBox.StandardButton.Yes:del self.commands[self.command_list.currentRow()];self.refresh_list()
class WhatIfDialog(QDialog):
    def __init__(self,parent=None):super().__init__(parent);self.setWindowTitle("What-If Calculator");self.amount=0;layout=QVBoxLayout(self);label=QLabel("Enter a hypothetical EXTRA monthly payment:");self.amount_input=QDoubleSpinBox();self.amount_input.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.PlusMinus);self.amount_input.setSingleStep(10);self.amount_input.setRange(0.01,1e9);self.amount_input.setDecimals(2);self.amount_input.setValue(100.0);button_box=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel);button_box.accepted.connect(self.accept);button_box.rejected.connect(self.reject);layout.addWidget(label);layout.addWidget(self.amount_input);layout.addWidget(button_box)
    def accept(self):self.amount=self.amount_input.value();super().accept()

# --- MAIN APPLICATION WINDOW ---
class MainWindow(QMainWindow):
    def __init__(self, **managers):
        super().__init__(); [setattr(self, name, instance) for name, instance in managers.items()]
        self.ai_analyser = FinancialAnalyser(api_key=self.config.get("OPENROUTER_API_KEY"))
        if not self.config.get("OPENROUTER_API_KEY"): self.show_api_key_dialog(is_first_run=True)
        self.setWindowTitle("Finance Board"); self.setWindowIcon(QIcon("assets/icon.ico"))
        self.setMinimumSize(1000, 750); self.resize(1400, 900)
        self.create_menu_bar(); self.setStatusBar(QStatusBar(self))
        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        self.tabs.addTab(self.create_dashboard_tab(), "Dashboard"); self.tabs.addTab(self.create_ledger_tab(), "Ledger & Transactions"); self.tabs.addTab(self.create_journal_tab(), "Journal")
        self.tabs.currentChanged.connect(self.refresh_ui); self.refresh_ui()

    def create_menu_bar(self):
        menu_bar=self.menuBar();s=self.style();file_menu=menu_bar.addMenu("File");tools_menu=menu_bar.addMenu("Tools");ai_menu=menu_bar.addMenu("AI Tools")
        save_action=QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)),"Save",self);save_action.setShortcut(QKeySequence.StandardKey.Save);save_action.triggered.connect(self.save_and_refresh);file_menu.addAction(save_action)
        export_action=QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ArrowUp)),"Export All to CSV",self);export_action.triggered.connect(self.export_all_data);file_menu.addAction(export_action)
        file_menu.addSeparator() # --- NEW ---
        api_key_action = QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)), "Set API Key...", self); api_key_action.triggered.connect(self.show_api_key_dialog); file_menu.addAction(api_key_action)
        file_menu.addSeparator() # --- NEW ---
        clear_action=QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)),"Clear All Data...",self);clear_action.triggered.connect(self.clear_all_data);file_menu.addAction(clear_action)
        snowball_action=QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_MediaSeekForward)),"Debt Payoff Strategy",self);snowball_action.triggered.connect(self.show_debt_snowball);tools_menu.addAction(snowball_action)
        whatif_action=QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)),"What-If Calculator",self);whatif_action.triggered.connect(self.show_what_if_calc);tools_menu.addAction(whatif_action)
        networth_action=QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ToolBarVerticalExtensionButton)),"Log Net Worth Snapshot",self);networth_action.triggered.connect(self.log_net_worth);tools_menu.addAction(networth_action)
        health_check_action=QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)),"Get Financial Health Check",self);health_check_action.triggered.connect(self.run_ai_health_check);ai_menu.addAction(health_check_action)
        chat_action=QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)),"Start AI Chat",self);chat_action.triggered.connect(self.run_ai_chat);ai_menu.addAction(chat_action)
        command_bar_action=QAction(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_CommandLink)),"Use AI Command Bar",self);command_bar_action.triggered.connect(self.run_ai_command_bar);ai_menu.addAction(command_bar_action)

    def create_dashboard_tab(self):
        widget=QWidget();main_layout=QVBoxLayout(widget);title=QLabel("Finance Board Dashboard");title.setObjectName("Header");main_layout.addWidget(title,alignment=Qt.AlignmentFlag.AlignHCenter);top_layout=QHBoxLayout();summary_container=QWidget();summary_layout=QFormLayout(summary_container);self.summary_labels={'debt_incurred':QLabel(),'debt_paid':QLabel(),'debt_remaining':QLabel(),'debt_eta':QLabel(),'loan_out':QLabel(),'loan_repaid':QLabel(),'loan_remaining':QLabel(),'net_position':QLabel()};[l.setFont(QFont("Segoe UI",11))for l in self.summary_labels.values()];self.summary_labels['net_position'].setFont(QFont("Segoe UI",12,QFont.Weight.Bold));summary_layout.addRow(QLabel());summary_layout.addRow(QLabel("<b>DEBTS (Money You Owe)</b>"));summary_layout.addRow("Total Debt Incurred:",self.summary_labels['debt_incurred']);summary_layout.addRow("Total Payments Made:",self.summary_labels['debt_paid']);summary_layout.addRow("<b>Remaining Debt Balance:</b>",self.summary_labels['debt_remaining']);summary_layout.addRow("<i>Est. Debt-Free Date:</i>",self.summary_labels['debt_eta']);summary_layout.addRow(QLabel());summary_layout.addRow(QLabel("<b>LOANS (Money Owed to You)</b>"));summary_layout.addRow("Total Loaned Out:",self.summary_labels['loan_out']);summary_layout.addRow("Total Repaid to You:",self.summary_labels['loan_repaid']);summary_layout.addRow("<b>Remaining to Collect:</b>",self.summary_labels['loan_remaining']);summary_layout.addRow(QLabel());summary_layout.addRow(QLabel("---"));summary_layout.addRow("<h2>Net Financial Position:</h2>",self.summary_labels['net_position']);top_layout.addWidget(summary_container,1);self.pie_chart_canvas=self.create_pie_chart();top_layout.addWidget(self.pie_chart_canvas,1);main_layout.addLayout(top_layout);self.line_chart_canvas=self.create_line_chart();main_layout.addWidget(self.line_chart_canvas,1);return widget
    
    def create_pie_chart(self):
        fig,self.pie_ax=plt.subplots(facecolor='#2e3440');self.pie_ax.set_facecolor('#2e3440');return FigureCanvas(fig)
    
    def create_line_chart(self):
        fig,self.line_ax=plt.subplots(facecolor='#2e3440');self.line_ax.set_facecolor('#2e3440');return FigureCanvas(fig)
    
    def create_ledger_tab(self):
        widget=QWidget();layout=QHBoxLayout(widget);self.list_widget=QListWidget();self.list_widget.currentItemChanged.connect(self.on_selection_changed);self.details_panel=self.create_details_panel();layout.addWidget(self.list_widget,1);layout.addWidget(self.details_panel,2);return widget
    
    def create_details_panel(self):
        s=self.style();container=QWidget();layout=QVBoxLayout(container);self.detail_label=QLabel("No item selected");self.detail_label.setObjectName("SubHeader");self.detail_balance=QLabel();self.detail_info=QLabel();self.detail_info.setWordWrap(True);layout.addWidget(self.detail_label);layout.addWidget(self.detail_balance);layout.addWidget(self.detail_info);trans_label=QLabel("Transactions");trans_label.setStyleSheet("font-size:12pt;margin-top:15px;");self.transaction_list_widget=QListWidget();layout.addWidget(trans_label);layout.addWidget(self.transaction_list_widget,1);self.add_transaction_btn=QPushButton("Add Payment/Repayment");self.add_transaction_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)));self.add_transaction_btn.clicked.connect(self.add_transaction);self.add_transaction_btn.setEnabled(False);crud_layout=QHBoxLayout();add_btn=QPushButton("Add Entry");add_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileIcon)));edit_btn=QPushButton("Edit Entry");edit_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_DialogResetButton)));delete_btn=QPushButton("Delete Entry");delete_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)));add_btn.clicked.connect(self.add_entry);edit_btn.clicked.connect(self.edit_entry);delete_btn.clicked.connect(self.delete_entry);crud_layout.addStretch();crud_layout.addWidget(add_btn);crud_layout.addWidget(edit_btn);crud_layout.addWidget(delete_btn);layout.addWidget(self.add_transaction_btn);layout.addLayout(crud_layout);return container
    
    def create_journal_tab(self):
        s=self.style();widget=QWidget();layout=QVBoxLayout(widget);title=QLabel("Financial Journal");title.setObjectName("Header");layout.addWidget(title);self.journal_list=QListWidget();self.journal_list.setWordWrap(True);self.journal_list.currentItemChanged.connect(self.on_journal_selection_changed);layout.addWidget(self.journal_list,1);btn_layout=QHBoxLayout();add_btn=QPushButton("Add Entry");add_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon)));add_btn.clicked.connect(self.add_journal_entry);self.delete_journal_btn=QPushButton("Delete Selected Entry");self.delete_journal_btn.setIcon(QIcon(s.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)));self.delete_journal_btn.clicked.connect(self.delete_journal_entry);self.delete_journal_btn.setEnabled(False);btn_layout.addStretch();btn_layout.addWidget(add_btn);btn_layout.addWidget(self.delete_journal_btn);layout.addLayout(btn_layout);return widget

    def refresh_ui(self, index=None):
        if index is None: index = self.tabs.currentIndex()
        if index == 0: self.refresh_dashboard()
        elif index == 1: self.refresh_ledger_list()
        elif index == 2: self.refresh_journal_list()
    def refresh_dashboard(self):
        all_e=self.ledger_manager.get_all_entries();all_t=self.transaction_manager.get_all_transactions();debt_e=[e for e in all_e if e.entry_type=='debt'];loan_e=[e for e in all_e if e.entry_type=='loan'];debt_bal=sum(calculate_balance_for_entry(d,all_t)for d in debt_e);loan_bal=sum(calculate_balance_for_entry(l,all_t)for l in loan_e);net_pos=loan_bal-debt_bal;total_debt=calculate_total_entry_amount(debt_e);total_paid=calculate_total_transaction_amount([t for t in all_t if t.transaction_type=='payment']);total_loaned=calculate_total_entry_amount(loan_e);total_repaid=calculate_total_transaction_amount([t for t in all_t if t.transaction_type=='repayment']);self.summary_labels['debt_incurred'].setText(f"${total_debt:,.2f}");self.summary_labels['debt_paid'].setText(f"${total_paid:,.2f}");self.summary_labels['debt_remaining'].setText(f"${debt_bal:,.2f}");self.summary_labels['debt_eta'].setText(calculate_overall_eta(debt_e,[t for t in all_t if t.transaction_type=='payment']));self.summary_labels['loan_out'].setText(f"${total_loaned:,.2f}");self.summary_labels['loan_repaid'].setText(f"${total_repaid:,.2f}");self.summary_labels['loan_remaining'].setText(f"${loan_bal:,.2f}");self.summary_labels['net_position'].setText(f"${net_pos:,.2f}")
        self.pie_ax.clear();self.pie_ax.set_title('Debt vs. Loans Balance',color='white');
        if debt_bal>0 or loan_bal>0:self.pie_ax.pie([debt_bal,loan_bal],labels=['Total Debt','Total Loans'],autopct='%1.1f%%',startangle=90,colors=['#bf616a','#a3be8c'],textprops={'color':'white'})
        else:self.pie_ax.text(0.5,0.5,'No Data',ha='center',va='center',color='gray')
        self.pie_chart_canvas.draw()
        self.line_ax.clear();self.line_ax.set_title('Net Worth Over Time',color='white');self.line_ax.tick_params(axis='x',colors='white');self.line_ax.tick_params(axis='y',colors='white');self.line_ax.spines['bottom'].set_color('#d8dee9');self.line_ax.spines['left'].set_color('#d8dee9');self.line_ax.spines['top'].set_color('#2e3440');self.line_ax.spines['right'].set_color('#2e3440');snapshots=self.net_worth_manager.get_all_snapshots()
        if len(snapshots)>1:dates=[s.date_recorded for s in snapshots];values=[s.net_position for s in snapshots];self.line_ax.plot(dates,values,marker='o',color='#88c0d0');self.line_ax.figure.autofmt_xdate()
        else:self.line_ax.text(0.5,0.5,'Log at least two snapshots to see a trend',ha='center',va='center',color='gray')
        self.line_chart_canvas.draw()
    def refresh_ledger_list(self):
        current_id=self.get_selected_entry_id();self.list_widget.clear();entries=self.ledger_manager.get_all_entries()
        if not entries: return
        for entry in sorted(entries,key=lambda e:e.label):
            item=QListWidgetItem(f"{entry.label} ({entry.status.capitalize()})");item.setData(Qt.ItemDataRole.UserRole,entry);self.list_widget.addItem(item)
            if entry.id==current_id:self.list_widget.setCurrentItem(item)
    def refresh_journal_list(self):
        current_id=self.get_selected_journal_id();self.journal_list.clear()
        for entry in self.journal_manager.get_all_entries():
            item=QListWidgetItem(f"{entry.date_created.strftime('%Y-%m-%d %H:%M')}\n{entry.content}");item.setData(Qt.ItemDataRole.UserRole,entry);self.journal_list.addItem(item)
            if entry.id==current_id:self.journal_list.setCurrentItem(item)

    def on_selection_changed(self,c,p):
        entry=self.get_selected_entry();self.transaction_list_widget.clear()
        if entry:self.add_transaction_btn.setEnabled(True);self.add_transaction_btn.setText(f"Add {'Payment' if entry.entry_type=='debt' else'Repayment'}");bal=calculate_balance_for_entry(entry,self.transaction_manager.get_all_transactions());self.detail_label.setText(entry.label);self.detail_balance.setText(f"Current Balance: ${bal:,.2f}");self.detail_info.setText(f"<b>Type:</b> {entry.entry_type.capitalize()}<br><b>Status:</b> {entry.status.capitalize()}<br><b>Tags:</b> {', '.join(entry.tags)if entry.tags else'None'}<br><b>Comments:</b> {entry.comments if entry.comments else'None'}");[self.transaction_list_widget.addItem(f"{t.date_paid.strftime('%Y-%m-%d')} - {t.label} (${t.amount:,.2f})")for t in sorted(self.transaction_manager.get_transactions_for_entry(entry.id),key=lambda t:t.date_paid,reverse=True)]
        else:self.add_transaction_btn.setEnabled(False);self.detail_label.setText("No item selected");self.detail_balance.setText("");self.detail_info.setText("")
    def on_journal_selection_changed(self):self.delete_journal_btn.setEnabled(bool(self.journal_list.currentItem()))

    def add_entry(self):
        dialog=EntryDialog(self.tag_manager,parent=self);
        if dialog.exec():self.ledger_manager.add_entry(**dialog.entry_data);self.save_and_refresh()

    def edit_entry(self):
        entry=self.get_selected_entry();
        if not entry:QMessageBox.warning(self,"No Selection","Please select an entry to edit.");return
        dialog=EntryDialog(self.tag_manager,entry=entry,parent=self)
        if dialog.exec():data=dialog.entry_data;entry.label=data['label'];entry.amount=data['amount'];entry.entry_type=data['entry_type'];entry.comments=data['comments'];entry.tags=data['tags'];self.update_entry_status(entry);self.save_and_refresh()
    def delete_entry(self):
        entry=self.get_selected_entry()
        if not entry:QMessageBox.warning(self,"No Selection","Please select an entry to delete.");return
        if QMessageBox.question(self,"Confirm Delete",f"Delete '{entry.label}'?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:self.ledger_manager.delete_entry_by_id(entry.id);self.transaction_manager.delete_transactions_by_entry_id(entry.id);self.save_and_refresh()
    def add_transaction(self):
        entry=self.get_selected_entry();
        if not entry:return
        dialog=TransactionDialog(self)
        if dialog.exec():trans_type="payment" if entry.entry_type=='debt' else'repayment';self.transaction_manager.add_transaction(entry_id=entry.id,transaction_type=trans_type,**dialog.transaction_data);self.update_entry_status(entry);self.save_and_refresh()
    def add_journal_entry(self):
        text,ok=QInputDialog.getMultiLineText(self,"New Journal Entry","Enter your thoughts or notes:")
        if ok and text:self.journal_manager.add_entry(text);self.save_and_refresh()
    def delete_journal_entry(self):
        item=self.journal_list.currentItem();
        if not item:return
        entry=item.data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self,"Confirm Delete","Delete this journal entry?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:self.journal_manager.delete_entry_by_id(entry.id);self.save_and_refresh()
    def clear_all_data(self):
        if QMessageBox.critical(self,"Confirm Clear All Data","WARNING: This will permanently delete ALL data. This action cannot be undone. Are you absolutely sure?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)==QMessageBox.StandardButton.Yes:self.ledger_manager.entries.clear();self.transaction_manager.transactions.clear();self.journal_manager.entries.clear();self.net_worth_manager.snapshots.clear();self.save_and_refresh()
    def export_all_data(self):
        path=QFileDialog.getExistingDirectory(self,"Select Export Directory")
        if path:
            try:export_data_to_csv(self.ledger_manager,self.transaction_manager,path);QMessageBox.information(self,"Export Successful",f"Data successfully exported to:\n{path}")
            except Exception as e:QMessageBox.critical(self,"Export Failed",f"An error occurred: {e}")
    def show_debt_snowball(self):
        active_debts=[e for e in self.ledger_manager.get_all_entries() if e.entry_type=='debt' and e.status=='active'];
        if not active_debts:QMessageBox.information(self,"Debt Strategy","Congratulations! You have no active debts.");return
        priority_debt=suggest_snowball_priority(active_debts,self.transaction_manager.get_all_transactions())
        if priority_debt:bal=calculate_balance_for_entry(priority_debt,self.transaction_manager.get_all_transactions());QMessageBox.information(self,"Debt Payoff Strategy",f"Using the Snowball method, your priority should be:\n\n<b>{priority_debt.label}</b>\nRemaining Balance: ${bal:,.2f}")
        else:QMessageBox.information(self,"Debt Strategy","Congratulations! All your active debts have a zero or negative balance.")
    def show_what_if_calc(self):
        dialog=WhatIfDialog(self)
        if dialog.exec():eta_string=calculate_what_if_eta(self.ledger_manager.get_all_entries(),self.transaction_manager.get_all_transactions(),dialog.amount);QMessageBox.information(self,"What-If Result",eta_string)
    def log_net_worth(self):
        all_entries=self.ledger_manager.get_all_entries();all_trans=self.transaction_manager.get_all_transactions();debt_bal=sum(calculate_balance_for_entry(e,all_trans)for e in all_entries if e.entry_type=='debt');loan_bal=sum(calculate_balance_for_entry(e,all_trans)for e in all_entries if e.entry_type=='loan');net_pos=loan_bal-debt_bal;self.net_worth_manager.add_snapshot(net_pos);QMessageBox.information(self,"Net Worth Logged",f"Successfully logged a new net worth snapshot of ${net_pos:,.2f}.");self.save_and_refresh()
    def run_ai_health_check(self):
        if not self.ai_analyser.api_key:QMessageBox.warning(self,"AI Disabled","Please set your API key first.");return
        report=self.ai_analyser.generate_insights(self.ledger_manager.get_all_entries(),self.transaction_manager.get_all_transactions());msg_box=QMessageBox(self);msg_box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);msg_box.setWindowTitle("AI Financial Health Check");msg_box.setText(report);msg_box.exec()
    def run_ai_chat(self):
        if not self.ai_analyser.api_key:QMessageBox.warning(self,"AI Disabled","Please set your API key first.");return
        dialog=AiChatDialog(self.ai_analyser,self.ledger_manager,self.transaction_manager,self);dialog.exec()
    def run_ai_command_bar(self):
        if not self.ai_analyser.api_key:QMessageBox.warning(self,"AI Disabled","Please set your API key first.");return
        command_str,ok=QInputDialog.getText(self,"AI Command Bar","Enter a command (e.g., 'add $50 debt for groceries'):")
        if not(ok and command_str):return
        parsed=self.ai_analyser.parse_command_to_json(command_str);commands=parsed.get("commands",[])
        if not commands:QMessageBox.warning(self,"AI Command Error","Sorry, I couldn't understand that command.");return
        msg_box=QMessageBox(self);msg_box.setWindowTitle("Confirm AI Plan");msg_box.setText("The AI understood the following plan. Proceed?")
        plan_text="\n".join([f"Step {i+1}: {c.get('action','?').replace('_',' ').title()} with details: {c.get('payload',{})}"for i,c in enumerate(commands)])
        msg_box.setInformativeText(plan_text);yes_btn=msg_box.addButton("Yes",QMessageBox.ButtonRole.YesRole);edit_btn=msg_box.addButton("Edit Plan...",QMessageBox.ButtonRole.ActionRole);msg_box.addButton("Cancel",QMessageBox.ButtonRole.NoRole);msg_box.exec()
        if msg_box.clickedButton()==yes_btn:self.execute_ai_plan(commands)
        elif msg_box.clickedButton()==edit_btn:
            editor=AiPlanEditorDialog(commands,self.tag_manager,self)
            if editor.exec():self.execute_ai_plan(editor.commands)
    def execute_ai_plan(self,commands):
        for command in commands:
            try:
                if command['action']=='add_entry':self.ledger_manager.add_entry(**command['payload'])
            except Exception as e:QMessageBox.critical(self,"Execution Error",f"Failed to execute command: {command}\nError: {e}");return
        self.save_and_refresh();QMessageBox.information(self,"AI Command Executed","The AI commands were executed successfully.")
    
    def save_and_refresh(self):self.storage_manager.save_data(self.ledger_manager,self.transaction_manager,self.journal_manager,self.net_worth_manager);self.refresh_ui();self.statusBar().showMessage("Data Saved!",2000)
    def get_selected_entry(self):item=self.list_widget.currentItem();return item.data(Qt.ItemDataRole.UserRole)if item else None
    def get_selected_entry_id(self):entry=self.get_selected_entry();return entry.id if entry else None
    def get_selected_journal_id(self):item=self.journal_list.currentItem();return item.data(Qt.ItemDataRole.UserRole).id if item else None
    def closeEvent(self,event):self.save_and_refresh();super().closeEvent(event)
    
    def show_api_key_dialog(self, is_first_run=False): 
        current_key = self.config.get("OPENROUTER_API_KEY", "")
        dialog = ApiKeyDialog(current_key=current_key, parent=self)
        if dialog.exec():
            self.config["OPENROUTER_API_KEY"]=dialog.api_key;save_config(self.config);self.ai_analyser.api_key=dialog.api_key;QMessageBox.information(self,"Success","API Key saved!")
        elif is_first_run:
            QMessageBox.warning(self,"AI Disabled","No API key provided. AI features will be disabled.")
    
    def check_and_request_api_key(self):
        # This method is now simplified in the __init__ call
        pass