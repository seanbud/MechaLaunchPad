import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QTextEdit, QProgressBar, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from app.core.resources import StyleTokens
from app.services.gitlab_service import GitLabService, CIPollingWorker

class CIJobCard(QFrame):
    dismiss_requested = Signal()

    def __init__(self, service: GitLabService, category: str, branch_name: str, parent=None):
        super().__init__(parent)
        self.service = service
        self.category = category
        self.branch_name = branch_name
        self.worker = None
        self.is_finished = False
        self.status_val = "pending"
        self.web_url = ""
        
        self.setStyleSheet(f"background-color: #28272d; border: 1px solid {StyleTokens.BORDER}; border-radius: 6px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Header Row
        header_layout = QHBoxLayout()
        
        # Data Labels
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        
        cat_label = QLabel(category.upper())
        cat_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {StyleTokens.TEXT_MAIN}; border: none; background: transparent;")
        title_layout.addWidget(cat_label)
        
        branch_label = QLabel(branch_name)
        branch_label.setStyleSheet(f"font-size: 11px; color: {StyleTokens.TEXT_SECONDARY}; border: none; background: transparent;")
        title_layout.addWidget(branch_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Status Label
        self.status_icon = QLabel("⏳")
        self.status_icon.setStyleSheet("font-size: 20px; border: none; background: transparent;")
        header_layout.addWidget(self.status_icon)
        
        self.status_label = QLabel("Pending")
        self.status_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {StyleTokens.WARNING}; border: none; background: transparent;")
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Actions Row
        actions_layout = QHBoxLayout()
        self.link_btn = QPushButton("View in GitLab")
        self.link_btn.setEnabled(False)
        self.link_btn.clicked.connect(self.open_link)
        actions_layout.addWidget(self.link_btn)
        
        actions_layout.addStretch()
        
        self.dismiss_btn = QPushButton("Dismiss")
        self.dismiss_btn.hide() # Only show when finished
        self.dismiss_btn.clicked.connect(self.dismiss_requested.emit)
        self.dismiss_btn.setStyleSheet(f"color: {StyleTokens.TEXT_SECONDARY}; border: 1px solid {StyleTokens.BORDER};")
        actions_layout.addWidget(self.dismiss_btn)
        
        self.toggle_logs_btn = QPushButton("Show Logs")
        self.toggle_logs_btn.clicked.connect(self.toggle_logs)
        actions_layout.addWidget(self.toggle_logs_btn)
        
        layout.addLayout(actions_layout)
        
        # Logs View (Terminal style)
        self.logs_view = QTextEdit()
        self.logs_view.setReadOnly(True)
        self.logs_view.setAcceptRichText(True)
        self.logs_view.setMinimumHeight(150)
        self.logs_view.hide()
        
        # Terminal Bezel Styling
        self.logs_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0c0c0d;
                color: #d1d1d1;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        layout.addWidget(self.logs_view)
        
        # Start Worker
        self.logs_view.append(f"Starting tracking for {branch_name}...\n")
        self.worker = CIPollingWorker(self.service, self.branch_name)
        self.worker.status_updated.connect(self.on_pipeline_status)
        self.worker.error.connect(self.on_pipeline_error)
        self.worker.start()

    def open_link(self):
        if self.web_url:
            QDesktopServices.openUrl(QUrl(self.web_url))

    def toggle_logs(self):
        if self.logs_view.isHidden():
            self.logs_view.show()
            self.toggle_logs_btn.setText("Hide Logs")
        else:
            self.logs_view.hide()
            self.toggle_logs_btn.setText("Show Logs")

    def on_pipeline_status(self, data):
        status = data.get("status")
        self.status_val = status
        self.web_url = data.get("web_url", "")
        
        if self.web_url:
            self.link_btn.setEnabled(True)
            
        icon = "❓"
        if status in ("running", "pending"):
            icon = "🔄" if status == "running" else "⏳"
            color = StyleTokens.WARNING
        elif status == "success":
            icon = "✅"
            color = StyleTokens.SUCCESS
        elif status in ("failed", "canceled"):
            icon = "❌" if status == "failed" else "🚫"
            color = StyleTokens.ERROR

        self.status_icon.setText(icon)
        self.status_label.setText(status.capitalize())
        self.status_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color}; border: none; background: transparent;")

        # Update Logs (HTML Terminal)
        jobs = data.get("jobs", [])
        html_logs = "<style>b { color: #58a6ff; }</style><b>[PIPELINE STATUS: " + status.upper() + "]</b><br>"
        
        if not jobs:
            html_logs += f"<br><span style='color: {StyleTokens.TEXT_SECONDARY};'>Allocating remote runner...</span>"
        else:
            for job in jobs:
                j_status = job.get("status")
                j_name = job.get("name")
                j_stage = job.get("stage")
                
                j_symbol = "⏳"
                j_color = "#888"
                if j_status == "success": j_symbol, j_color = "✅", StyleTokens.SUCCESS
                elif j_status == "failed": j_symbol, j_color = "❌", StyleTokens.ERROR
                elif j_status == "running": j_symbol, j_color = "🔄", StyleTokens.WARNING
                
                html_logs += f"<div style='margin-bottom: 2px;'><span style='color: {j_color};'>{j_symbol}</span> <b>{j_name}</b> <span style='color: #555;'>({j_stage})</span></div>"

        self.logs_view.setHtml(html_logs)

        if status in ("success", "failed", "canceled"):
            self.is_finished = True
            self.dismiss_btn.show()
            if self.worker:
                self.worker.stop()

    def on_pipeline_error(self, error):
        self.logs_view.append(f"[ERROR] {error}")
        self.status_icon.setText("⚠️")
        self.status_label.setText("Error")
        self.status_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {StyleTokens.ERROR}; border: none; background: transparent;")
        self.is_finished = True
        self.status_val = "error"
        self.dismiss_btn.show()

    def stop_worker(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()

class CITab(QWidget):
    job_cleared = Signal(str) # Emits branch_name when a module is cleared

    def __init__(self, service: GitLabService):
        super().__init__()
        self.service = service
        self.cards = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header Row
        header_layout = QHBoxLayout()
        header = QLabel("Continuous Integration Status")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {StyleTokens.PRIMARY};")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        clear_btn = QPushButton("Clear Finished")
        clear_btn.clicked.connect(self.clear_finished)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll Area for Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.addStretch() # Push cards to top
        
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

    def track_branch(self, category, branch_name):
        """Called by MainWindow when a new publish finishes or on boot to track a pipeline."""
        # Prevent duplicate tracking for same branch
        for card in self.cards:
            if card.branch_name == branch_name:
                return
                
        card = CIJobCard(self.service, category, branch_name)
        card.dismiss_requested.connect(lambda c=card: self.remove_card(c))
        # Insert before the stretch
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)
        self.cards.append(card)

    def remove_card(self, card):
        if card in self.cards:
            self.cards.remove(card)
        self.scroll_layout.removeWidget(card)
        self.job_cleared.emit(card.branch_name)
        card.stop_worker()
        card.deleteLater()

    def clear_finished(self):
        # Create a copy since we will mutate the list during iteration
        for card in list(self.cards):
            if card.is_finished and card.status_val == "success":
                self.remove_card(card)
