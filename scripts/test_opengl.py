import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from app.viewport import ModularViewport

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("OpenGL Viewport Test")
    window.resize(800, 600)
    
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    
    label = QLabel("Orbit: Left Click | Pan: Middle Click | Zoom: Scroll")
    label.setStyleSheet("color: white; background: #222; padding: 5px;")
    layout.addWidget(label)
    
    viewport = ModularViewport()
    layout.addWidget(viewport)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
