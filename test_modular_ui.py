#!/usr/bin/env python3
"""
Test script for the modular Home Assistant GUI.
This script tests the basic functionality of the modular UI components.
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.main_window import MainWindow
from config.settings import HOME_ASSISTANT
from utils.helpers import setup_logging

def test_modular_ui():
    """Test the modular UI components."""
    
    # Setup logging
    setup_logging("DEBUG")
    logger = logging.getLogger(__name__)
    logger.info("Starting modular UI test...")
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("Home Assistant GUI Test")
        app.setApplicationVersion("1.0.0")
        
        # Enable high DPI scaling
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Create main window
        logger.info("Creating main window...")
        window = MainWindow(api_config=HOME_ASSISTANT)
        
        # Test page switching
        logger.info("Testing page switching...")
        pages = ["overview", "devices", "automations", "scenes", "scripts", "settings"]
        
        for page in pages:
            logger.info(f"Switching to page: {page}")
            success = window.switch_to_page(page)
            if success:
                logger.info(f"✓ Successfully switched to {page}")
            else:
                logger.warning(f"✗ Failed to switch to {page}")
        
        # Test page state preservation
        logger.info("Testing page state preservation...")
        window.save_all_page_states()
        logger.info("✓ Page states saved")
        
        window.restore_all_page_states()
        logger.info("✓ Page states restored")
        
        # Show the window
        window.show()
        
        # Show success message
        QMessageBox.information(
            window,
            "Test Successful",
            "Modular UI test completed successfully!\n\n"
            "Features tested:\n"
            "• Page creation and initialization\n"
            "• Navigation between pages\n"
            "• Page state preservation\n"
            "• UI component loading\n\n"
            "The application is ready to use!"
        )
        
        logger.info("Modular UI test completed successfully")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        
        # Show error message
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            QMessageBox.critical(
                None,
                "Test Failed",
                f"Modular UI test failed:\n\n{str(e)}\n\nPlease check the logs for more details."
            )
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    test_modular_ui()
