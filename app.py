import logging
import warnings
from PySide6.QtWidgets import QApplication
from ui.dashboard import Dashboard

def main():
    app = QApplication([])
    window = Dashboard()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
