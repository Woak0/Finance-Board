import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Financial Assistant")
        self.resize(1024, 768)

