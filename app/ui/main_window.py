import os
import json
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, 
    QStatusBar, QPushButton, QHBoxLayout, QComboBox, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QThread, Signal
from app.core.resources import QSS_STYLE, StyleTokens
from app.services.blender_launcher import BlenderLauncher
from app.services.template_service import TemplateService
from app.services.validation_service import ValidationService
from app.ui.viewport import ModularViewport
from validation.models import Severity, FBXData

# The ExportTab class has been removed as per user request. 
# Its functionality is now integrated into the PreviewTab.

class ValidationWorker(QThread):
    finished = Signal(list, object, str) # results, fbx_data, error

    def __init__(self, service, fbx_path, category):
        super().__init__()
        self.service = service
        self.fbx_path = fbx_path
        self.category = category

    def run(self):
        results, fbx_data, error = self.service.validate_fbx(self.fbx_path, self.category)
        self.finished.emit(results, fbx_data, error)

class RobotAssemblyWorker(QThread):
    """Loads the base robot model and extracts all parts."""
    finished = Signal(dict, str) # category -> fbx_data, error

    def __init__(self, service, base_fbx):
        super().__init__()
        self.service = service
        self.base_fbx = base_fbx

    def run(self):
        # We use the same service but iterate through all categories
        results = {}
        error_msg = None
        
        # Load the FBX once to get raw data
        success, stdout, stderr = self.service.launcher.run_python_script(
            self.service.extract_script,
            extra_args=[self.base_fbx]
        )
        
        if success != 0:
            self.finished.emit({}, f"Failed to load base robot: {stderr}")
            return

        # Parse JSON
        try:
            lines = stdout.splitlines()
            start_idx = lines.index("RESULT_START")
            fbx_json = json.loads(lines[start_idx + 1])
            
            raw_data = FBXData(
                filename=fbx_json["filename"],
                tris=fbx_json["tris"],
                meshes=fbx_json["meshes"],
                armature_name=fbx_json["armature_name"],
                bones=fbx_json["bones"]
            )
            
            # Now split by category based on registry
            categories = ["LeftArm", "RightArm", "Torso", "Head", "Legs"]
            for cat in categories:
                _, filtered_fbx = self.service.runner.validate(self.base_fbx, raw_data, cat)
                results[cat] = filtered_fbx
                
            self.finished.emit(results, "")
        except Exception as e:
            self.finished.emit({}, f"Error processing base robot: {e}")

class PreviewTab(QWidget):
    def __init__(self, viewport: ModularViewport, template_service: TemplateService):
        super().__init__()
        self.viewport = viewport
        self.template_service = template_service
        self.custom_parts = {} # category -> fbx_data
        self.default_parts = {} # category -> fbx_data
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet(f"background-color: {StyleTokens.BG_LEVEL_2}; border-right: 1px solid {StyleTokens.BORDER};")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(20, 20, 20, 20)
        side_layout.setSpacing(15)
        
        header = QLabel("Robot Assembly")
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {StyleTokens.PRIMARY};")
        side_layout.addWidget(header)
        
        self.selectors = {}
        for cat in ["Head", "Torso", "LeftArm", "RightArm", "Legs"]:
            cat_group = QWidget()
            group_layout = QVBoxLayout(cat_group)
            group_layout.setContentsMargins(0, 5, 0, 5)
            
            label = QLabel(cat)
            label.setStyleSheet("font-weight: bold;")
            group_layout.addWidget(label)
            
            combo = QComboBox()
            combo.addItems(["Default", "Custom"])
            combo.setEnabled(False) # Enable once we have custom parts
            combo.currentIndexChanged.connect(lambda idx, c=cat: self.on_part_swapped(c, idx))
            group_layout.addWidget(combo)
            
            self.selectors[cat] = combo
            side_layout.addWidget(cat_group)
            
        side_layout.addStretch()
        
        # Export Module at the bottom of sidebar (Refined)
        export_group = QWidget()
        export_layout = QVBoxLayout(export_group)
        export_layout.setContentsMargins(0, 20, 0, 0)
        export_layout.setSpacing(12)
        
        export_header = QLabel("Export Template")
        export_header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {StyleTokens.PRIMARY};")
        export_layout.addWidget(export_header)
        
        export_desc = QLabel("Export the current robot assembly into a Blender template with the full mech rig.")
        export_desc.setStyleSheet(f"color: {StyleTokens.TEXT_SECONDARY}; font-size: 11px;")
        export_desc.setWordWrap(True)
        export_layout.addWidget(export_desc)
        
        self.export_btn = QPushButton("Generate Template")
        self.export_btn.setObjectName("primary_action")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setStyleSheet(f"background-color: {StyleTokens.SUCCESS}; color: white; border: none; font-size: 14px; font-weight: bold;")
        self.export_btn.clicked.connect(self.on_export_clicked)
        export_layout.addWidget(self.export_btn)
        
        side_layout.addWidget(export_group)
        
        layout.addWidget(sidebar)
        
        # Main Viewport Wrapper (to allow overlay or toolbar)
        view_container = QWidget()
        view_layout = QVBoxLayout(view_container)
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.setSpacing(0)
        
        controls = QLabel("🖱️ Left Click: Orbit  |  Middle Click: Pan  |  Scroll: Zoom")
        controls.setAlignment(Qt.AlignCenter)
        controls.setStyleSheet(f"background-color: {StyleTokens.BG_LEVEL_2}; border-bottom: 1px solid {StyleTokens.BORDER}; color: {StyleTokens.TEXT_SECONDARY}; padding: 8px; font-weight: bold;")
        view_layout.addWidget(controls)
        
        view_layout.addWidget(self.viewport, 1)
        layout.addWidget(view_container, 1)

    def on_export_clicked(self):
        dest_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not dest_dir:
            return
            
        self.export_btn.setEnabled(False)
        self.export_btn.setText("Generating...")
        
        # Export the whole rig template
        # Passing empty string to trigger full rig export setup (if script supports it)
        # Or defaulting to a core part like Torso or "All" depending on what the script needs
        path, error = self.template_service.generate_template("ALL", dest_dir)
        
        self.export_btn.setEnabled(True)
        self.export_btn.setText("Generate Template")
        
        if path:
            QMessageBox.information(self, "Success", f"Template generated successfully:\n{path}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to generate template:\n{error}")

    def on_part_swapped(self, category, index):
        """Swaps between default and custom mesh for a limb."""
        if index == 0: # Default
            data = self.default_parts.get(category)
        else: # Custom
            data = self.custom_parts.get(category)
            
        if data:
            self.viewport.load_fbx_data(category, data)

    def set_default_assembly(self, assembly):
        self.default_parts = assembly
        for cat, data in assembly.items():
            self.viewport.load_fbx_data(cat, data)
            
    def add_custom_part(self, category, fbx_data, filename="Custom", filepath=None):
        self.custom_parts[category] = fbx_data
        combo = self.selectors.get(category)
        if combo:
            combo.setEnabled(True)
            if combo.count() > 1:
                combo.setItemText(1, filename)
            else:
                combo.addItem(filename)
            combo.setCurrentIndex(1) # Auto-switch to custom when validated
            self.on_part_swapped(category, 1)

class ValidateTab(QWidget):
    validation_success = Signal(str, object, str, str) # category, fbx_data, filename, filepath
    
    def __init__(self, service: ValidationService):
        super().__init__()
        self.service = service
        self.fbx_path = ""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Validate Asset")
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {StyleTokens.PRIMARY};")
        layout.addWidget(header)
        
        # Selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No FBX file selected")
        self.file_label.setStyleSheet(f"color: {StyleTokens.TEXT_SECONDARY}; font-style: italic;")
        self.file_label.setTextFormat(Qt.RichText)
        file_layout.addWidget(self.file_label, 1)
        
        select_btn = QPushButton("Select FBX...")
        select_btn.clicked.connect(self.on_select_file)
        file_layout.addWidget(select_btn)
        layout.addLayout(file_layout)
        
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Target Category:"))
        self.part_selector = QComboBox()
        self.part_selector.addItems(["LeftArm", "RightArm", "Torso", "Head", "Legs"])
        self.part_selector.setFixedWidth(200)
        form_layout.addWidget(self.part_selector)
        form_layout.addStretch()
        layout.addLayout(form_layout)
        
        # Action
        self.validate_btn = QPushButton("Run Preflight Check")
        self.validate_btn.setObjectName("primary_action")
        self.validate_btn.setFixedWidth(200)
        self.validate_btn.setEnabled(False)
        self.validate_btn.clicked.connect(self.on_validate_clicked)
        layout.addWidget(self.validate_btn)
        
        # Results
        layout.addWidget(QLabel("Validation Results:"))
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"background-color: {StyleTokens.BG_LEVEL_1}; border: 1px solid {StyleTokens.BORDER};")
        layout.addWidget(self.results_list)

    def on_select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select authored FBX", "", "FBX Files (*.fbx)")
        if path:
            self.fbx_path = path
            fname = os.path.basename(path)
            self.file_label.setText(f"<b>Selected:</b> <span style='color: {StyleTokens.PRIMARY};'>{fname}</span>")
            self.file_label.setStyleSheet(f"color: {StyleTokens.TEXT_MAIN}; font-style: normal;")
            self.validate_btn.setEnabled(True)
            self.results_list.clear() # Clear old results on new selection

    def on_validate_clicked(self):
        self.results_list.clear()
        self.validate_btn.setEnabled(False)
        self.validate_btn.setText("Validating...")
        
        category = self.part_selector.currentText()
        
        # Run validation in background
        self.worker = ValidationWorker(self.service, self.fbx_path, category)
        self.worker.finished.connect(self.on_validation_finished)
        self.worker.start()

    def on_validation_finished(self, results, fbx_data, error):
        self.validate_btn.setEnabled(True)
        self.validate_btn.setText("Run Preflight Check")
        
        category = self.part_selector.currentText()
        
        if error:
            item = QListWidgetItem(f"ERROR: {error}")
            item.setForeground(QColor(StyleTokens.ERROR))
            self.results_list.addItem(item)
            return

        all_passed = all(r.passed for r in results if r.severity == Severity.ERROR)
        
        for res in results:
            color = QColor(StyleTokens.TEXT_MAIN)
            prefix = "✓" if res.passed else "✗"
            
            if not res.passed:
                color = QColor(StyleTokens.ERROR) if res.severity == Severity.ERROR else QColor(StyleTokens.WARNING)
            
            item = QListWidgetItem(f"{prefix} [{res.rule_id}] {res.message}")
            item.setForeground(color)
            self.results_list.addItem(item)
            
            if res.fix_hint:
                hint = QListWidgetItem(f"   ↳ Fix: {res.fix_hint}")
                hint.setForeground(QColor(StyleTokens.TEXT_SECONDARY))
                self.results_list.addItem(hint)
        
        if fbx_data and all_passed:
            fname = os.path.basename(self.fbx_path)
            self.validation_success.emit(category, fbx_data, fname, self.fbx_path)

class TabPlaceholder(QWidget):
    def __init__(self, title, description):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        header = QLabel(title)
        header.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {StyleTokens.PRIMARY};")
        
        desc = QLabel(description)
        desc.setStyleSheet(f"color: {StyleTokens.TEXT_SECONDARY}; margin-bottom: 20px;")
        desc.setWordWrap(True)
        
        layout.addWidget(header)
        layout.addWidget(desc)
        
        btn = QPushButton(f"Enter {title}")
        btn.setFixedWidth(200)
        layout.addWidget(btn)

from app.ui.publish_tab import PublishTab
from app.ui.ci_tab import CITab
from app.services.gitlab_service import GitLabService

from app.core.state_manager import StateManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MechaLaunchPad — Modular Pipeline")
        self.resize(1000, 750)
        
        # Initialize Services
        try:
            self.launcher = BlenderLauncher()
            self.template_service = TemplateService(self.launcher)
            self.validation_service = ValidationService(self.launcher)
            self.gitlab_service = GitLabService() # Loads from env if available
            self.state_manager = StateManager()
        except Exception as e:
            QMessageBox.critical(self, "Tools Missing", f"Could not initialize MechaBridge:\n{e}")
            import sys
            sys.exit(1)
        
        # Apply Global Styles
        self.setStyleSheet(QSS_STYLE)
        
        # Central Tab Widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Initialize Tabs
        self.init_tabs()
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        if self.gitlab_service.repo_url and self.gitlab_service.token:
            self.statusBar().showMessage("Ready — Connected to GitLab API")
        else:
            self.statusBar().showMessage("Ready — GitLab credentials missing (.env)")

    def init_tabs(self):
        self.viewport = ModularViewport()
        self.preview_tab = PreviewTab(self.viewport, self.template_service)
        self.tabs.addTab(self.preview_tab, "📦 Preview && Export")

        
        validate_tab = ValidateTab(self.validation_service)
        self.tabs.addTab(validate_tab, "✅ Validate")
        
        # Wire validation to preview
        validate_tab.validation_success.connect(self.preview_tab.add_custom_part)
        
        # New Feature Tabs
        self.publish_tab = PublishTab(self.gitlab_service)
        self.ci_tab = CITab(self.gitlab_service)
        
        self.tabs.addTab(self.publish_tab, "🚀 Publish")
        self.tabs.addTab(self.ci_tab, "📊 CI Status")
        
        # Wire Validation Tab to Publish Tab
        validate_tab.validation_success.connect(self.publish_tab.on_validation_success)
        
        # Wire validation to state manager
        validate_tab.validation_success.connect(
            lambda cat, fbx, fn, fp: self.state_manager.add_validated_part(cat, fn, fp, fbx)
        )
        
        # Wire Publish Tab to state manager and CI tab
        self.publish_tab.submission_started.connect(self.ci_tab.track_branch)
        self.publish_tab.submission_started.connect(self.state_manager.add_tracked_ci)
        self.publish_tab.part_published.connect(self.state_manager.remove_validated_part)
        
        # Wire CI Tab cleanup to state manager
        self.ci_tab.job_cleared.connect(self.state_manager.remove_tracked_ci)
        
        # Load persistent state into tabs
        validated_state = self.state_manager.state.get("validated_parts", [])
        self.publish_tab.load_state(validated_state)
        
        # Also re-hydrate the Preview/Export tab dropdowns with validated parts
        from validation.models import FBXData
        for part in validated_state:
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
            # This automatically populates the dropdown list and enables it
            self.preview_tab.add_custom_part(
                category=part.get("category"),
                fbx_data=fbx_data,
                filename=part.get("filename"),
                filepath=part.get("filepath")
            )
            
        all_ci = self.state_manager.get_all_tracked_ci()
        for ci in all_ci:
            self.ci_tab.track_branch(ci["category"], ci["branch_name"])
        
        # Start background load of base robot
        self.load_base_robot()

    def load_base_robot(self):
        base_path = os.path.join(os.getcwd(), "data", "Basic_Model.fbx")
        if not os.path.exists(base_path):
            self.statusBar().showMessage("Warning: Basic_Model.fbx not found.")
            return
            
        self.statusBar().showMessage("Loading base robot assembly...")
        self.robot_worker = RobotAssemblyWorker(self.validation_service, base_path)
        self.robot_worker.finished.connect(self.on_base_robot_loaded)
        self.robot_worker.start()

    def on_base_robot_loaded(self, assembly, error):
        if error:
            self.statusBar().showMessage(f"Assembly Error: {error}")
            QMessageBox.warning(self, "Load Error", error)
        else:
            self.preview_tab.set_default_assembly(assembly)
            
            # Preserve GitLab status
            if self.gitlab_service.repo_url and self.gitlab_service.token:
                self.statusBar().showMessage("Robot assembly complete. | Ready — Connected to GitLab API")
            else:
                self.statusBar().showMessage("Robot assembly complete. | Ready — GitLab credentials missing (.env)")

    def on_validation_success(self, category, fbx_data):
        """Deprecated: Now handled by preview_tab.add_custom_part"""
        pass
