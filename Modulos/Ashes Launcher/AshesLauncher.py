# AshesLauncher.py
import sys
from PySide6.QtWidgets import QApplication
from Views.MainWindow import LauncherMainView

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LauncherMainView()
    window.show()
    sys.exit(app.exec())