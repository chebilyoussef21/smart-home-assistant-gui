# utils/helpers.py

import logging
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'ha_gui.log')),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file {config_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading config file {config_path}: {e}")
        return {}

def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """Save configuration to JSON file."""
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving config file {config_path}: {e}")
        return False

def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        if timestamp.endswith('Z'):
            timestamp = timestamp[:-1] + '+00:00'
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError):
        return timestamp

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def validate_entity_id(entity_id: str) -> bool:
    """Validate Home Assistant entity ID format."""
    if not entity_id or '.' not in entity_id:
        return False
    
    domain, object_id = entity_id.split('.', 1)
    
    # Check domain
    if not domain or not domain.replace('_', '').isalnum():
        return False
    
    # Check object_id
    if not object_id or not object_id.replace('_', '').isalnum():
        return False
    
    return True

def get_entity_domain(entity_id: str) -> Optional[str]:
    """Get the domain from an entity ID."""
    if '.' in entity_id:
        return entity_id.split('.')[0]
    return None

def get_entity_object_id(entity_id: str) -> Optional[str]:
    """Get the object ID from an entity ID."""
    if '.' in entity_id:
        return entity_id.split('.', 1)[1]
    return None

def is_controllable_entity(entity_id: str) -> bool:
    """Check if an entity is controllable."""
    controllable_domains = {
        'light', 'switch', 'fan', 'cover', 'lock', 'climate',
        'media_player', 'camera', 'alarm_control_panel', 'input_boolean',
        'input_number', 'input_select', 'input_text', 'scene'
    }
    
    domain = get_entity_domain(entity_id)
    return domain in controllable_domains if domain else False

def is_sensor_entity(entity_id: str) -> bool:
    """Check if an entity is a sensor."""
    sensor_domains = {
        'sensor', 'binary_sensor', 'weather', 'sun', 'moon'
    }
    
    domain = get_entity_domain(entity_id)
    return domain in sensor_domains if domain else False

def get_entity_icon(entity_id: str, attributes: Dict[str, Any]) -> str:
    """Get the appropriate icon for an entity."""
    # Check if entity has a custom icon
    if 'icon' in attributes:
        return attributes['icon']
    
    # Get domain-based default icon
    domain = get_entity_domain(entity_id)
    if not domain:
        return 'mdi:help-circle'
    
    domain_icons = {
        'light': 'mdi:lightbulb',
        'switch': 'mdi:power',
        'fan': 'mdi:fan',
        'cover': 'mdi:window-shutter',
        'lock': 'mdi:lock',
        'climate': 'mdi:thermostat',
        'media_player': 'mdi:play',
        'camera': 'mdi:camera',
        'alarm_control_panel': 'mdi:shield-home',
        'sensor': 'mdi:gauge',
        'binary_sensor': 'mdi:checkbox-marked-circle',
        'weather': 'mdi:weather-cloudy',
        'sun': 'mdi:weather-sunny',
        'moon': 'mdi:weather-night'
    }
    
    return domain_icons.get(domain, 'mdi:help-circle')

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage."""
    import re
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Ensure it's not empty
    if not filename:
        filename = 'unnamed'
    return filename

def get_file_size_human_readable(size_bytes: int) -> str:
    """Convert file size in bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def retry_on_exception(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on exception."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator

def ensure_directory_exists(directory_path: str) -> bool:
    """Ensure a directory exists, create if it doesn't."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        return False

def get_resource_path(relative_path: str) -> str:
    """Get the absolute path to a resource file."""
    import sys
    
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Development environment
        base_path = os.path.dirname(os.path.dirname(__file__))
    
    return os.path.join(base_path, relative_path)
