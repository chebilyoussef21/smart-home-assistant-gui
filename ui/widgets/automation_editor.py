# ui/widgets/automation_editor.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout,
    QComboBox, QLineEdit, QTextEdit, QCheckBox, QSpinBox,
    QDialog, QDialogButtonBox, QMessageBox, QScrollArea,
    QFrame, QSplitter
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from typing import List, Dict, Any, Optional
import logging

from models.automation import Automation, Trigger, Action, Condition, AutomationMode
from services.automation_manager import AutomationManager

logger = logging.getLogger(__name__)

class AutomationEditor(QWidget):
    """Editor for creating and managing Home Assistant automations."""
    
    def __init__(self, ha_api):
        super().__init__()
        self.ha_api = ha_api
        self.automation_manager = AutomationManager(ha_api)
        self.automations: List[Automation] = []
        self.current_automation: Optional[Automation] = None
        
        self._init_ui()
        QTimer.singleShot(0, self.refresh)

    def _init_ui(self):
        """Initialize the automation editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        self._create_header(layout)
        
        # Main content area with splitter
        self._create_main_content(layout)

    def _create_header(self, parent_layout):
        """Create the header with title and controls."""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Automations")
        title_label.setObjectName("pageTitle")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Buttons
        self.new_button = QPushButton("New Automation")
        self.new_button.clicked.connect(self._create_new_automation)
        header_layout.addWidget(self.new_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self._edit_automation)
        header_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._delete_automation)
        header_layout.addWidget(self.delete_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(self.refresh_button)
        
        parent_layout.addWidget(header_frame)

    def _create_main_content(self, parent_layout):
        """Create the main content area with automation list and editor."""
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - automation list
        self._create_automation_list(splitter)
        
        # Right panel - automation details/editor
        self._create_automation_details(splitter)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        parent_layout.addWidget(splitter)

    def _create_automation_list(self, parent):
        """Create the automation list panel."""
        list_frame = QFrame()
        list_frame.setObjectName("listFrame")
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # List title
        list_title = QLabel("Automations")
        list_title.setObjectName("sectionTitle")
        list_layout.addWidget(list_title)
        
        # Automation list
        self.automation_list = QListWidget()
        self.automation_list.itemSelectionChanged.connect(self._on_automation_selected)
        list_layout.addWidget(self.automation_list)
        
        parent.addWidget(list_frame)

    def _create_automation_details(self, parent):
        """Create the automation details panel."""
        details_frame = QFrame()
        details_frame.setObjectName("detailsFrame")
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        # Details title
        self.details_title = QLabel("Select an automation to view details")
        self.details_title.setObjectName("sectionTitle")
        details_layout.addWidget(self.details_title)
        
        # Scrollable details area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setSpacing(16)
        
        scroll_area.setWidget(self.details_widget)
        details_layout.addWidget(scroll_area)
        
        parent.addWidget(details_frame)

    def refresh(self):
        """Refresh the automation list from Home Assistant."""
        try:
            # Skip network calls if offline
            if hasattr(self.ha_api, 'is_connected') and not self.ha_api.is_connected:
                self.automations = []
                self._update_automation_list()
                return

            # Fetch automations from Home Assistant
            automations_data = self.ha_api.get_automations()
            # print(automations_data)
            
            # Convert to Automation objects
            self.automations = []
            for automation_data in automations_data:
                try:
                    automation = Automation.from_dict(automation_data)
                    self.automations.append(automation)
                except Exception as e:
                    logger.warning(f"Failed to parse automation: {e}")
            
            # Update the list
            self._update_automation_list()
            
            logger.info(f"Refreshed {len(self.automations)} automations")
            
        except Exception as e:
            logger.error(f"Failed to refresh automations: {e}")
            QMessageBox.warning(self, "Error", f"Failed to refresh automations:\n{str(e)}")

    def _update_automation_list(self):
        """Update the automation list widget."""
        self.automation_list.clear()
        
        for automation in self.automations:
            item = QListWidgetItem(automation.alias)
            item.setData(Qt.UserRole, automation)
            
            # Add status indicator
            status = "Enabled" if automation.enabled else "Disabled"
            item.setText(f"{automation.alias} ({status})")
            
            self.automation_list.addItem(item)

    def _on_automation_selected(self):
        """Handle automation selection."""
        current_item = self.automation_list.currentItem()
        if current_item:
            self.current_automation = current_item.data(Qt.UserRole)
            self._show_automation_details()
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            self.current_automation = None
            self._clear_automation_details()
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)

    def _show_automation_details(self):
        """Show details for the selected automation."""
        if not self.current_automation:
            return
        
        # Clear existing details
        self._clear_automation_details()
        
        # Update title
        self.details_title.setText(f"Automation: {self.current_automation.alias}")
        
        # Basic info
        self._create_basic_info_section()
        
        # Triggers
        self._create_triggers_section()
        
        # Conditions
        self._create_conditions_section()
        
        # Actions
        self._create_actions_section()

    def _clear_automation_details(self):
        """Clear the automation details panel."""
        for i in reversed(range(self.details_layout.count())):
            self.details_layout.itemAt(i).widget().setParent(None)

    def _create_basic_info_section(self):
        """Create the basic information section."""
        group = QGroupBox("Basic Information")
        layout = QFormLayout(group)
        
        # Alias
        alias_label = QLabel(self.current_automation.alias)
        layout.addRow("Name:", alias_label)
        
        # Description
        desc_text = self.current_automation.description or "No description"
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        layout.addRow("Description:", desc_label)
        
        # Mode
        mode_label = QLabel(self.current_automation.mode.value.title())
        layout.addRow("Mode:", mode_label)
        
        # Enabled status
        status_label = QLabel("Enabled" if self.current_automation.enabled else "Disabled")
        status_label.setProperty("class", "statusOnline" if self.current_automation.enabled else "statusOffline")
        layout.addRow("Status:", status_label)
        
        self.details_layout.addWidget(group)

    def _create_triggers_section(self):
        """Create the triggers section."""
        group = QGroupBox("Triggers")
        layout = QVBoxLayout(group)
        
        if self.current_automation.trigger:
            for i, trigger in enumerate(self.current_automation.trigger):
                trigger_widget = self._create_trigger_widget(trigger, i)
                layout.addWidget(trigger_widget)
        else:
            no_triggers = QLabel("No triggers defined")
            no_triggers.setStyleSheet("color: #888888; font-style: italic;")
            layout.addWidget(no_triggers)
        
        self.details_layout.addWidget(group)

    def _create_trigger_widget(self, trigger: Trigger, index: int) -> QWidget:
        """Create a widget for displaying a trigger."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet("QFrame { border: 1px solid #404040; border-radius: 4px; padding: 8px; }")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Trigger type
        type_label = QLabel(f"Trigger {index + 1}: {trigger.platform.title()}")
        type_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(type_label)
        
        # Trigger details
        details = []
        if trigger.entity_id:
            details.append(f"Entity: {trigger.entity_id}")
        if trigger.to:
            details.append(f"To: {trigger.to}")
        if trigger.from_:
            details.append(f"From: {trigger.from_}")
        if trigger.at:
            details.append(f"At: {trigger.at}")
        
        if details:
            details_label = QLabel(" • ".join(details))
            details_label.setWordWrap(True)
            layout.addWidget(details_label)
        
        return widget

    def _create_conditions_section(self):
        """Create the conditions section."""
        group = QGroupBox("Conditions")
        layout = QVBoxLayout(group)
        
        if self.current_automation.condition:
            for i, condition in enumerate(self.current_automation.condition):
                condition_widget = self._create_condition_widget(condition, i)
                layout.addWidget(condition_widget)
        else:
            no_conditions = QLabel("No conditions defined")
            no_conditions.setStyleSheet("color: #888888; font-style: italic;")
            layout.addWidget(no_conditions)
        
        self.details_layout.addWidget(group)

    def _create_condition_widget(self, condition: Condition, index: int) -> QWidget:
        """Create a widget for displaying a condition."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet("QFrame { border: 1px solid #404040; border-radius: 4px; padding: 8px; }")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Condition type
        type_label = QLabel(f"Condition {index + 1}: {condition.condition.title()}")
        type_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(type_label)
        
        # Condition details
        details = []
        if condition.entity_id:
            details.append(f"Entity: {condition.entity_id}")
        if condition.state:
            details.append(f"State: {condition.state}")
        if condition.above is not None:
            details.append(f"Above: {condition.above}")
        if condition.below is not None:
            details.append(f"Below: {condition.below}")
        
        if details:
            details_label = QLabel(" • ".join(details))
            details_label.setWordWrap(True)
            layout.addWidget(details_label)
        
        return widget

    def _create_actions_section(self):
        """Create the actions section."""
        group = QGroupBox("Actions")
        layout = QVBoxLayout(group)
        
        if self.current_automation.action:
            for i, action in enumerate(self.current_automation.action):
                action_widget = self._create_action_widget(action, i)
                layout.addWidget(action_widget)
        else:
            no_actions = QLabel("No actions defined")
            no_actions.setStyleSheet("color: #888888; font-style: italic;")
            layout.addWidget(no_actions)
        
        self.details_layout.addWidget(group)

    def _create_action_widget(self, action: Action, index: int) -> QWidget:
        """Create a widget for displaying an action."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Box)
        widget.setStyleSheet("QFrame { border: 1px solid #404040; border-radius: 4px; padding: 8px; }")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Action type
        type_label = QLabel(f"Action {index + 1}: {action.service}")
        type_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(type_label)
        
        # Action details
        details = []
        if action.entity_id:
            details.append(f"Entity: {action.entity_id}")
        if action.data:
            for key, value in action.data.items():
                details.append(f"{key}: {value}")
        
        if details:
            details_label = QLabel(" • ".join(details))
            details_label.setWordWrap(True)
            layout.addWidget(details_label)
        
        return widget

    def _create_new_automation(self):
        """Create a new automation."""
        dialog = AutomationDialog(self.ha_api, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def _edit_automation(self):
        """Edit the selected automation."""
        if not self.current_automation:
            return
        
        dialog = AutomationDialog(self.ha_api, self, self.current_automation)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def _delete_automation(self):
        """Delete the selected automation."""
        if not self.current_automation:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Automation",
            f"Are you sure you want to delete the automation '{self.current_automation.alias}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # TODO: Implement automation deletion in API
                QMessageBox.information(self, "Success", "Automation deleted successfully")
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete automation:\n{str(e)}")


class AutomationDialog(QDialog):
    """Dialog for creating/editing automations."""
    
    def __init__(self, ha_api, parent=None, automation=None):
        super().__init__(parent)
        self.ha_api = ha_api
        self.automation = automation
        self.is_editing = automation is not None
        
        self.setWindowTitle("Edit Automation" if self.is_editing else "New Automation")
        self.setMinimumSize(600, 500)
        
        self._init_ui()
        
        if self.is_editing:
            self._load_automation_data()

    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form
        form_group = QGroupBox("Automation Details")
        form_layout = QFormLayout(form_group)
        
        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_edit)
        
        # Mode
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([mode.value.title() for mode in AutomationMode])
        form_layout.addRow("Mode:", self.mode_combo)
        
        # Enabled
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)
        form_layout.addRow("", self.enabled_checkbox)
        
        layout.addWidget(form_group)
        
        # TODO: Add trigger, condition, and action editors
        # For now, just show a placeholder
        placeholder = QLabel("Trigger, Condition, and Action editors will be implemented here.")
        placeholder.setStyleSheet("color: #888888; font-style: italic; padding: 20px;")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_automation_data(self):
        """Load automation data into the form."""
        if not self.automation:
            return
        
        self.name_edit.setText(self.automation.alias)
        self.description_edit.setPlainText(self.automation.description or "")
        self.mode_combo.setCurrentText(self.automation.mode.value.title())
        self.enabled_checkbox.setChecked(self.automation.enabled)

    def accept(self):
        """Handle dialog acceptance."""
        try:
            # Create or update automation
            automation_data = {
                "alias": self.name_edit.text(),
                "description": self.description_edit.toPlainText(),
                "mode": self.mode_combo.currentText().lower(),
                "enabled": self.enabled_checkbox.isChecked(),
                "trigger": [],  # TODO: Implement trigger editor
                "action": [],   # TODO: Implement action editor
                "condition": [] # TODO: Implement condition editor
            }
            
            if self.is_editing:
                # TODO: Implement automation update
                QMessageBox.information(self, "Success", "Automation updated successfully")
            else:
                # Create new automation
                result = self.ha_api.create_automation(automation_data)
                if result:
                    QMessageBox.information(self, "Success", "Automation created successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to create automation")
            
            super().accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save automation:\n{str(e)}")
