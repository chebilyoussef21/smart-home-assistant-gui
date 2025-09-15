# ui/main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSplitter, QStackedWidget, QStatusBar, QMessageBox,
    QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
import os
import sys
import logging

from services.ha_api import HomeAssistantAPI
from ui.widgets.navigation_sidebar import NavigationSidebar
from ui.widgets.page_stack_manager import PageStackManager
from ui.widgets.overview_page import OverviewPage
from ui.widgets.device_grid import DeviceGridView
from ui.widgets.automation_editor import AutomationEditor
from ui.widgets.scenes_page import ScenesPage
from ui.widgets.scripts_page import ScriptsPage
from ui.widgets.settings_panel import SettingsPanel
from config.settings import HOME_ASSISTANT, UI

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window for the Home Assistant GUI application with modular page system."""
    
    def __init__(self, api_config=None):
        super().__init__()
        self.api_config = api_config or HOME_ASSISTANT
        # self.api_config = api_config
        self.ui_config = UI
        
        # Initialize Home Assistant API
        self.ha_api = HomeAssistantAPI(
            host=self.api_config["host"],
            token=self.api_config["api_token"],
            timeout=self.api_config.get("timeout", 10),
            use_websocket=self.api_config.get("use_websocket", True)
        )
        
        self.setWindowTitle("Home Assistant GUI")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Apply stylesheet
        self._apply_stylesheet()
        
        # Initialize UI
        self._init_ui()
        self._setup_pages()
        self._setup_navigation()
        self._setup_status_bar()

        # Connect API signals after UI and status bar are ready
        self.ha_api.connection_status_changed.connect(self._on_connection_status_changed)
        self.ha_api.error_occurred.connect(self._on_error_occurred)
        
        # Start refresh timer
        self._setup_refresh_timer()
        
        # Test initial connection
        self._test_connection()

    def _apply_stylesheet(self):
        """Apply the dark theme stylesheet."""
        stylesheet_path = os.path.join(os.path.dirname(__file__), "..", "assets", "stylesheet", "styles.qss")
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path, 'r') as f:
                self.setStyleSheet(f.read())

    def _init_ui(self):
        """Initialize the main UI components."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Create navigation sidebar
        self._create_navigation_sidebar()
        
        # Create main content area with page stack
        self._create_content_area()
        
        # Set splitter proportions
        self.splitter.setSizes([280, 920])

    def _create_navigation_sidebar(self):
        """Create the navigation sidebar."""
        self.navigation_sidebar = NavigationSidebar(self)
        self.navigation_sidebar.setMaximumWidth(300)
        self.navigation_sidebar.setMinimumWidth(250)
        
        # Add to splitter
        self.splitter.addWidget(self.navigation_sidebar)

    def _create_content_area(self):
        """Create the main content area with page stack."""
        # Create stacked widget for pages
        self.content_stack = QStackedWidget()
        
        # Create page stack manager
        self.page_manager = PageStackManager(self.content_stack)
        
        # Connect page manager signals
        self.page_manager.page_changed.connect(self._on_page_changed)
        self.page_manager.page_state_saved.connect(self._on_page_state_saved)
        self.page_manager.page_state_restored.connect(self._on_page_state_restored)
        
        # Add to splitter
        self.splitter.addWidget(self.content_stack)

    def _setup_pages(self):
        """Setup all the pages in the application."""
        try:
            # Create page instances
            self.overview_page = OverviewPage(self.ha_api)
            self.devices_page = DeviceGridView(self.ha_api)
            self.automations_page = AutomationEditor(self.ha_api)
            self.scenes_page = ScenesPage(self.ha_api)
            self.scripts_page = ScriptsPage(self.ha_api)
            self.settings_page = SettingsPanel(self.ha_api, self.api_config)
            
            # Add pages to the page manager
            self.page_manager.add_page("overview", self.overview_page)
            self.page_manager.add_page("devices", self.devices_page)
            self.page_manager.add_page("automations", self.automations_page)
            self.page_manager.add_page("scenes", self.scenes_page)
            self.page_manager.add_page("scripts", self.scripts_page)
            self.page_manager.add_page("settings", self.settings_page)
            
            logger.info("All pages initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup pages: {e}")
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize pages:\n{str(e)}\n\nPlease check the logs for more details."
            )

    def _setup_navigation(self):
        """Setup navigation between pages."""
        # Connect navigation sidebar signals
        self.navigation_sidebar.page_requested.connect(self._on_page_requested)
        self.navigation_sidebar.refresh_requested.connect(self._on_refresh_requested)
        
        # Set initial page
        self.page_manager.switch_to_page("overview")
        self.navigation_sidebar.set_current_page("overview")

    def _on_page_requested(self, page_name: str):
        """Handle page navigation requests."""
        try:
            success = self.page_manager.switch_to_page(page_name)
            if success:
                logger.info(f"Switched to page: {page_name}")
            else:
                logger.error(f"Failed to switch to page: {page_name}")
        except Exception as e:
            logger.error(f"Error switching to page {page_name}: {e}")

    def _on_page_changed(self, page_name: str):
        """Handle page changes."""
        # Update navigation sidebar
        self.navigation_sidebar.set_current_page(page_name)
        
        # Update window title
        page_titles = {
            "overview": "Overview",
            "devices": "Devices",
            "automations": "Automations",
            "scenes": "Scenes",
            "scripts": "Scripts",
            "settings": "Settings"
        }
        
        title = page_titles.get(page_name, "Home Assistant GUI")
        self.setWindowTitle(f"Home Assistant GUI - {title}")

    def _on_page_state_saved(self, page_name: str, state: dict):
        """Handle page state save events."""
        logger.debug(f"Page state saved for {page_name}: {len(state)} items")

    def _on_page_state_restored(self, page_name: str, state: dict):
        """Handle page state restore events."""
        logger.debug(f"Page state restored for {page_name}: {len(state)} items")

    def _on_refresh_requested(self):
        """Handle refresh requests from navigation."""
        self.page_manager.refresh_current_page()

    def _setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connection status
        self.connection_label = QLabel("Connecting...")
        self.status_bar.addWidget(self.connection_label)
        
        # Current page info
        self.current_page_label = QLabel("")
        self.status_bar.addWidget(self.current_page_label)
        
        # Add stretch to push other widgets to the right
        self.status_bar.addPermanentWidget(QLabel(""))  # Spacer
        
        # Last update time
        self.update_label = QLabel("")
        self.status_bar.addPermanentWidget(self.update_label)

    def _setup_refresh_timer(self):
        """Setup automatic refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_data)
        refresh_interval = self.ui_config.get("refresh_interval", 5) * 1000  # Convert to milliseconds
        self.refresh_timer.start(refresh_interval)

    def _refresh_data(self):
        """Refresh data for the current page."""
        # Update last refresh time
        from datetime import datetime
        self.update_label.setText(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        
        # Update current page info
        current_page = self.page_manager.get_current_page_name()
        if current_page:
            self.current_page_label.setText(f"Page: {current_page.title()}")
        
        # Refresh current page
        self.page_manager.refresh_current_page()

    def _test_connection(self):
        """Test the initial connection to Home Assistant."""
        self.connection_label.setText("Testing connection...")
        
        # Test connection in a separate thread to avoid blocking UI
        QTimer.singleShot(100, self._perform_connection_test)

    def _perform_connection_test(self):
        """Perform the actual connection test."""
        try:
            config = self.ha_api.get_config()
            if config:
                self.connection_label.setText("✅ Connected")
                self.connection_label.setProperty("class", "statusOnline")
                self.status_bar.showMessage("Connected to Home Assistant", 3000)
            else:
                self.connection_label.setText("❌ Connection Failed")
                self.connection_label.setProperty("class", "statusOffline")
                self.status_bar.showMessage("Failed to connect to Home Assistant", 5000)
        except Exception as e:
            self.connection_label.setText("❌ Connection Error")
            self.connection_label.setProperty("class", "statusOffline")
            self.status_bar.showMessage(f"Connection error: {str(e)}", 5000)

    def _on_connection_status_changed(self, is_connected):
        """Handle connection status changes."""
        # Guard in case signals arrive before status bar is initialized
        if hasattr(self, 'connection_label') and hasattr(self, 'status_bar'):
            if is_connected:
                self.connection_label.setText("✅ Connected")
                self.connection_label.setProperty("class", "statusOnline")
                self.status_bar.showMessage("Connected to Home Assistant", 3000)
            else:
                self.connection_label.setText("❌ Disconnected")
                self.connection_label.setProperty("class", "statusOffline")
                self.status_bar.showMessage("Disconnected from Home Assistant", 5000)

    def _on_error_occurred(self, error_message):
        """Handle errors from the API."""
        if hasattr(self, 'status_bar'):
            self.status_bar.showMessage(f"Error: {error_message}", 5000)
        
        # Show error dialog for critical errors
        if "Connection lost" in error_message or "WebSocket" in error_message:
            if hasattr(self, 'status_bar'):
                QMessageBox.warning(
                    self,
                    "Connection Error",
                    f"Connection issue detected:\n{error_message}\n\nPlease check your Home Assistant configuration."
                )

    def get_current_page(self) -> str:
        """Get the current page name."""
        return self.page_manager.get_current_page_name() or ""

    def switch_to_page(self, page_name: str) -> bool:
        """Switch to a specific page."""
        return self.page_manager.switch_to_page(page_name)

    def refresh_current_page(self):
        """Refresh the current page."""
        self.page_manager.refresh_current_page()

    def save_all_page_states(self):
        """Save the state of all pages."""
        self.page_manager.save_all_states()

    def restore_all_page_states(self):
        """Restore the state of all pages."""
        self.page_manager.restore_all_states()

    def closeEvent(self, event):
        """Handle application close event."""
        try:
            # Save all page states before closing
            self.save_all_page_states()
            
            # Clean up API connections
            if hasattr(self, 'ha_api'):
                self.ha_api.close()
            
            # Stop refresh timer
            if hasattr(self, 'refresh_timer'):
                self.refresh_timer.stop()
            
            logger.info("Application closing gracefully")
            
        except Exception as e:
            logger.error(f"Error during application close: {e}")
        
        event.accept()