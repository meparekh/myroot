import sys
from PyQt6.QtWidgets import QApplication
from ui import DuplicateFinderUI

def main():
    app = QApplication(sys.argv)
    window = DuplicateFinderUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
