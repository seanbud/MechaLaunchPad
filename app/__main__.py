import sys
import os
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow

def main():
    # Set environment variables for high DPI
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setApplicationName("MechaLaunchPad")
    app.setOrganizationName("MechCorp")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
