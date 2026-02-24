import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QListWidget, QListWidgetItem, QPlainTextEdit, QMessageBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal
from app.core.resources import StyleTokens
from app.services.gitlab_service import GitLabService, PublishWorker

class PublishTab(QWidget):
    submission_started = Signal(str, str) # category, branch_name
    part_published = Signal(str) # filepath
    
    def __init__(self, service: GitLabService):
        super().__init__()
        self.service = service
        self.validated_parts = {} # path -> (category, fbx_data, filename)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Publish to Asset Repository")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {StyleTokens.PRIMARY};")
        layout.addWidget(header)
        
        info = QLabel("Validated parts are ready to be pushed to GitLab. Select one to proceed.")
        info.setStyleSheet(f"color: {StyleTokens.TEXT_SECONDARY};")
        layout.addWidget(info)
        
        # List of Validated Parts
        self.parts_list = QListWidget()
        self.parts_list.setStyleSheet(f"background-color: {StyleTokens.BG_LEVEL_1}; border: 1px solid {StyleTokens.BORDER};")
        self.parts_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.parts_list)
        
        # Commit Message
        msg_label = QLabel("Commit Message (Optional):")
        layout.addWidget(msg_label)
        
        self.commit_input = QPlainTextEdit()
        self.commit_input.setFixedHeight(80)
        self.commit_input.setPlaceholderText("Description of changes...")
        layout.addWidget(self.commit_input)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {StyleTokens.WARNING}; font-weight: bold;")
        btn_layout.addWidget(self.status_label, 1)
        
        self.publish_btn = QPushButton("Publish to GitLab")
        self.publish_btn.setObjectName("primary_action")
        self.publish_btn.setFixedWidth(200)
        self.publish_btn.setEnabled(False)
        self.publish_btn.clicked.connect(self.on_publish_clicked)
        btn_layout.addWidget(self.publish_btn)
        
        layout.addLayout(btn_layout)

    def load_state(self, validated_parts):
        """Loads validated parts from persistent state."""
        from validation.models import FBXData
        for part in validated_parts:
            # Reconstruct the FBXData object
            fbx_dict = part.get("fbx_data")
            fbx_data = None
            if fbx_dict:
                fbx_data = FBXData(
                    filename=fbx_dict.get("filename", ""),
                    tris=fbx_dict.get("tris", 0),
                    meshes=fbx_dict.get("meshes", []),
                    armature_name=fbx_dict.get("armature_name", ""),
                    bones=fbx_dict.get("bones", [])
                )
            
            # Use existing method to populate the list and internal dictionary
            self.on_validation_success(
                category=part.get("category"),
                fbx_data=fbx_data,
                filename=part.get("filename"),
                filepath=part.get("filepath")
            )

    def on_validation_success(self, category, fbx_data, filename, filepath):
        """Called externally when a validation passes."""
        if filepath not in self.validated_parts:
            self.validated_parts[filepath] = (category, fbx_data, filename)
            item = QListWidgetItem(f"[{category}] - {filename}")
            item.setData(Qt.UserRole, filepath)
            
            # Check if this item is already in the list to avoid duplicates
            items = self.parts_list.findItems(item.text(), Qt.MatchExactly)
            if not items:
                self.parts_list.addItem(item)
                
            self.status_label.setText("New validated asset available.")
            self.status_label.setStyleSheet(f"color: {StyleTokens.SUCCESS};")

    def on_selection_changed(self):
        selected = self.parts_list.selectedItems()
        self.publish_btn.setEnabled(len(selected) > 0)
        
    def on_publish_clicked(self):
        selected = self.parts_list.selectedItems()
        if not selected:
            return
            
        filepath = selected[0].data(Qt.UserRole)
        category, fbx_data, filename = self.validated_parts[filepath]
        message = self.commit_input.toPlainText().strip()
        
        # Disable UI
        self.publish_btn.setEnabled(False)
        self.parts_list.setEnabled(False)
        self.commit_input.setEnabled(False)
        self.status_label.setStyleSheet(f"color: {StyleTokens.WARNING};")
        
        # Start worker
        self.worker = PublishWorker(
            self.service, 
            category=category,
            fbx_data=fbx_data,
            fbx_filepath=filepath,
            message=message
        )
        self.worker.progress.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_publish_finished)
        self.worker.start()
        
    def on_worker_progress(self, msg):
        self.status_label.setText(msg)

    def on_publish_finished(self, success, message, branch_name):
        # Re-enable UI
        self.publish_btn.setEnabled(True)
        self.parts_list.setEnabled(True)
        self.commit_input.setEnabled(True)
        
        if success:
            self.status_label.setText(message)
            self.status_label.setStyleSheet(f"color: {StyleTokens.SUCCESS};")
            
            # Signal the CI tab or main window that we have a branch to track
            selected = self.parts_list.selectedItems()
            if selected:
                category = self.validated_parts[selected[0].data(Qt.UserRole)][0]
                self.submission_started.emit(category, branch_name)
                
            # Optionally remove from list after publish?
            row = self.parts_list.currentRow()
            if row >= 0:
                item = self.parts_list.takeItem(row)
                filepath = item.data(Qt.UserRole)
                del self.validated_parts[filepath]
                self.part_published.emit(filepath)
                
            QMessageBox.information(self, "Publish Success", message)
            self.commit_input.clear()
        else:
            self.status_label.setText("Publish failed.")
            self.status_label.setStyleSheet(f"color: {StyleTokens.ERROR};")
            QMessageBox.critical(self, "Publish Error", message)
