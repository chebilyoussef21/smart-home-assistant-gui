#Entry point

# main.py

import sys
import os
import logging
from PyQt5.QtWidgets import (QApplication, QMessageBox, QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.main_window import MainWindow
from config.settings import HOME_ASSISTANT
from utils.helpers import setup_logging, get_resource_path

def main():
    """Main entry point for the Home Assistant GUI application."""
    
    # Setup logging
    setup_logging("INFO")
    logger = logging.getLogger(__name__)
    logger.info("Starting Home Assistant GUI...")
    
    try:
        # Initialize Qt application
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        app = QApplication(sys.argv)
        app.setApplicationName("Home Assistant GUI")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Home Assistant GUI")
        
        # Set application icon if available
        icon_path = get_resource_path("assets/icons/home-automation.svg")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Enable high DPI scaling
        # app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        # app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create main window
        logger.info("Creating main window...")
        window = MainWindow(api_config=HOME_ASSISTANT)
        # window = MainWindow()
        window.show()
        
        logger.info("Application started successfully")
        
        # Run event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        
        # Show error dialog if possible
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            QMessageBox.critical(
                None,
                "Application Error",
                f"Failed to start the application:\n\n{str(e)}\n\nPlease check the logs for more details."
            )
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()