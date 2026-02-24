import os
import sys
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

def resize_icon(input_path, output_path, size=256):
    # Need a QApplication to use QPixmap/QImage properly in some environments
    app = QApplication(sys.argv)
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return False
        
    image = QImage(input_path)
    if image.isNull():
        print(f"Error: Failed to load {input_path}")
        return False
        
    scaled_image = image.scaled(size, size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    if scaled_image.save(output_path, "PNG"):
        print(f"Successfully saved resized icon to {output_path}")
        return True
    else:
        print(f"Error: Failed to save {output_path}")
        return False

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_p = os.path.join(base_dir, "sprites", "app-icon.png")
    output_p = os.path.join(base_dir, "sprites", "app-icon-256.png")
    resize_icon(input_p, output_p)
