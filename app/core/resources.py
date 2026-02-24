class StyleTokens:
    # GitHub Desktop-ish Dark Palette
    BG_LEVEL_1 = "#0d1117"  # Deepest background
    BG_LEVEL_2 = "#161b22"  # Main background
    BG_LEVEL_3 = "#21262d"  # Borders and secondary backgrounds
    
    # Accent Colors (GitHub Blue)
    PRIMARY = "#58a6ff"
    PRIMARY_HOVER = "#2f81f7"
    
    # Text
    TEXT_MAIN = "#c9d1d9"
    TEXT_SECONDARY = "#8b949e"
    TEXT_WHITE = "#ffffff"
    
    # State Colors
    SUCCESS = "#3fb950"
    ERROR = "#f85149"
    WARNING = "#d29922"
    BORDER = "#30363d"
    
    # Fonts
    FONT_MAIN = "Segoe UI"  # Professional Windows standard
    FONT_SIZE_BODY = 13
    FONT_SIZE_HEADER = 18

QSS_STYLE = f"""
QMainWindow {{
    background-color: {StyleTokens.BG_LEVEL_2};
    color: {StyleTokens.TEXT_MAIN};
}}

QTabWidget::pane {{
    border: 1px solid {StyleTokens.BORDER};
    background: {StyleTokens.BG_LEVEL_2};
    border-top: none;
}}

QTabBar::tab {{
    background: {StyleTokens.BG_LEVEL_2};
    color: {StyleTokens.TEXT_SECONDARY};
    padding: 10px 20px;
    margin-right: 2px;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    font-family: '{StyleTokens.FONT_MAIN}', sans-serif;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    color: {StyleTokens.TEXT_MAIN};
    border-bottom: 2px solid {StyleTokens.PRIMARY};
}}

QTabBar::tab:hover {{
    color: {StyleTokens.TEXT_MAIN};
    background: {StyleTokens.BG_LEVEL_3};
}}

QPushButton {{
    background-color: {StyleTokens.BG_LEVEL_3};
    border: 1px solid {StyleTokens.BORDER};
    border-radius: 6px;
    padding: 6px 12px;
    color: {StyleTokens.TEXT_MAIN};
    font-weight: 500;
    font-family: '{StyleTokens.FONT_MAIN}', sans-serif;
}}

QPushButton:hover {{
    background-color: {StyleTokens.BORDER};
    border-color: {StyleTokens.TEXT_SECONDARY};
}}

QPushButton#primary_action {{
    background-color: {StyleTokens.SUCCESS};
    color: {StyleTokens.TEXT_WHITE};
    border: none;
}}

QPushButton#primary_action:hover {{
    background-color: "#2ea043";
}}

QLabel {{
    color: {StyleTokens.TEXT_MAIN};
    font-family: '{StyleTokens.FONT_MAIN}', sans-serif;
}}

QPlainTextEdit, QTextEdit {{
    background-color: {StyleTokens.BG_LEVEL_1};
    border: 1px solid {StyleTokens.BORDER};
    border-radius: 6px;
    color: {StyleTokens.TEXT_MAIN};
    padding: 8px;
    font-family: 'Consolas', 'Courier New', monospace;
}}

QStatusBar {{
    background-color: {StyleTokens.BG_LEVEL_2};
    border-top: 1px solid {StyleTokens.BORDER};
    color: {StyleTokens.TEXT_SECONDARY};
}}

QComboBox {{
    background-color: {StyleTokens.BG_LEVEL_3};
    border: 1px solid {StyleTokens.BORDER};
    border-radius: 6px;
    padding: 6px 12px;
    color: {StyleTokens.TEXT_MAIN};
    font-family: '{StyleTokens.FONT_MAIN}', sans-serif;
}}

QComboBox:hover {{
    border-color: {StyleTokens.TEXT_SECONDARY};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox QAbstractItemView {{
    background-color: {StyleTokens.BG_LEVEL_3};
    border: 1px solid {StyleTokens.BORDER};
    color: {StyleTokens.TEXT_MAIN};
    selection-background-color: {StyleTokens.PRIMARY};
    padding: 4px;
}}

QListWidget {{
    background-color: {StyleTokens.BG_LEVEL_1};
    border: 1px solid {StyleTokens.BORDER};
    color: {StyleTokens.TEXT_MAIN};
    border-radius: 6px;
}}

QListWidget::item {{
    padding: 12px;
    border-bottom: 1px solid {StyleTokens.BORDER};
}}

QListWidget::item:selected {{
    background-color: {StyleTokens.PRIMARY};
    color: {StyleTokens.TEXT_WHITE};
    border-radius: 4px;
}}

QProgressBar {{
    border: 1px solid {StyleTokens.BORDER};
    border-radius: 6px;
    background-color: {StyleTokens.BG_LEVEL_1};
    text-align: center;
    color: {StyleTokens.TEXT_WHITE};
    font-weight: bold;
}}

QProgressBar::chunk {{
    background-color: {StyleTokens.PRIMARY};
    border-radius: 5px;
}}
"""

