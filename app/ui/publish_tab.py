import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QListWidget, QListWidgetItem, QPlainTextEdit, QMessageBox, QFrame
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal, QThread
from app.core.resources import StyleTokens
from app.services.gitlab_service import GitLabService, PublishWorker


class VersionQueryWorker(QThread):
    """Background worker to query existing versions for a category."""
    finished = Signal(str, list)  # category, versions_list
    
    def __init__(self, service: GitLabService, category: str):
        super().__init__()
        self.service = service
        self.category = category
    
    def run(self):
        try:
            versions = self.service.get_existing_versions(self.category)
            self.finished.emit(self.category, versions)
        except Exception as e:
            print(f"Version query failed: {e}")
            self.finished.emit(self.category, [])


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
        
        # Version Context Panel
        self.version_panel = QFrame()
        self.version_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {StyleTokens.BG_LEVEL_1};
                border: 1px solid {StyleTokens.BORDER};
                border-radius: 6px;
                padding: 12px;
            }}
        """)
        version_layout = QVBoxLayout(self.version_panel)
        version_layout.setContentsMargins(12, 8, 12, 8)
        version_layout.setSpacing(4)
        
        self.version_header = QLabel("")
        self.version_header.setStyleSheet(f"font-weight: bold; color: {StyleTokens.TEXT_MAIN}; border: none; padding: 0;")
        version_layout.addWidget(self.version_header)
        
        self.version_detail = QLabel("")
        self.version_detail.setStyleSheet(f"color: {StyleTokens.TEXT_SECONDARY}; font-size: 12px; border: none; padding: 0;")
        self.version_detail.setWordWrap(True)
        version_layout.addWidget(self.version_detail)
        
        self.version_panel.setVisible(False)
        layout.addWidget(self.version_panel)
        
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
        
        if selected:
            filepath = selected[0].data(Qt.UserRole)
            category = self.validated_parts[filepath][0]
            
            # Show loading state in version panel
            self.version_panel.setVisible(True)
            self.version_header.setText(f"⏳ Checking server for existing {category} versions...")
            self.version_detail.setText("")
            
            # Query versions in background
            self._version_worker = VersionQueryWorker(self.service, category)
            self._version_worker.finished.connect(self.on_versions_loaded)
            self._version_worker.start()
        else:
            self.version_panel.setVisible(False)
    
    def on_versions_loaded(self, category, versions):
        """Called when the version query background worker completes."""
        if not versions:
            self.version_header.setText(f"🆕 {category} — First submission!")
            self.version_header.setStyleSheet(f"font-weight: bold; color: {StyleTokens.SUCCESS}; border: none; padding: 0;")
            self.version_detail.setText("This will be published as v001.")
        else:
            count = len(versions)
            version_list = ", ".join(versions[-5:])  # Show last 5
            if count > 5:
                version_list = f"...{version_list}"
            
            next_num = max(int(v[1:]) for v in versions if v[1:].isdigit()) + 1
            next_ver = f"v{next_num:03d}"
            
            self.version_header.setText(f"📦 {category} — {count} version{'s' if count > 1 else ''} on server")
            self.version_header.setStyleSheet(f"font-weight: bold; color: {StyleTokens.WARNING}; border: none; padding: 0;")
            self.version_detail.setText(
                f"Existing: {version_list}\n"
                f"This will be published as {next_ver}. (Adds a new version, does not replace existing ones.)"
            )
        
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
                
            # Remove from list after publish
            row = self.parts_list.currentRow()
            if row >= 0:
                item = self.parts_list.takeItem(row)
                filepath = item.data(Qt.UserRole)
                del self.validated_parts[filepath]
                self.part_published.emit(filepath)
            
            # Hide version panel
            self.version_panel.setVisible(False)
                
            QMessageBox.information(self, "Publish Success", message)
            self.commit_input.clear()
        else:
            self.status_label.setText("Publish failed.")
            self.status_label.setStyleSheet(f"color: {StyleTokens.ERROR};")
            QMessageBox.critical(self, "Publish Error", message)
