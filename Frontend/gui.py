import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLayout, QWidget, QListWidget, QHBoxLayout, QLabel

class MainWindow(QMainWindow):
    def __init__(self, ledger_entries):
        """
        The main window for the Financial Co-Pilot application.
        """
        super().__init__()
        self.all_entries = ledger_entries

        # --- Main Window Configuration ---
        self.setWindowTitle("Financial Co-Pilot")
        self.resize(1024, 768)

        # --- Create Widgets (the individual UI elements) ---
        self.list_widget = QListWidget()
        self.details_label = QLabel("Select an item from the list to see details.")

        # --- Populate the List Widget ---
        for entry in self.all_entries:
            self.list_widget.addItem(entry.label)

        # --- Create Layout and Container ---
        layout = QHBoxLayout()
        
        container = QWidget()
        container.setLayout(layout)

        # --- Assemble the Layout ---
        
        layout.addWidget(self.list_widget)
        layout.addWidget(self.details_label)

        # --- Set the Final Central Widget ---
        self.setCentralWidget(container)
        
        

        

