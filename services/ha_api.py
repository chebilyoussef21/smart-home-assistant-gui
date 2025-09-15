#REST/WebSocket API Wrapper

# services/ha_api.py

import requests
import asyncio
import websockets
import threading
import json
import logging
from typing import Dict, List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

class HomeAssistantAPI(QObject):
    """Enhanced Home Assistant API with REST and WebSocket support."""
    
    # Signals for real-time updates
    entity_updated = pyqtSignal(dict)  # Emitted when an entity state changes
    connection_status_changed = pyqtSignal(bool)  # Emitted when connection status changes
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs
    
    def __init__(self, host: str, token: str, timeout: int = 10, use_websocket: bool = True):
        super().__init__()
        self.host = host.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.use_websocket = use_websocket
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # WebSocket connection
        self.websocket = None
        self.websocket_task = None
        self.is_connected = False
        
        # Connection monitoring
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self._check_connection)
        self.connection_timer.start(30000)  # Check every 30 seconds
        
        # Start WebSocket connection if enabled
        if self.use_websocket:
            self._start_websocket()

    def _check_connection(self):
        """Check if Home Assistant is reachable."""
        url = f"{self.host}/api/"
        was_connected = self.is_connected

        try:
            response = requests.get(url, headers=self.headers, timeout=5) #sends a GET with headers (including long-lived token) and a 5-second timeout.
            if response.status_code == 200: #If the API root replies 200, you’re considered “connected.
                self.is_connected = True
            elif response.status_code in (401, 403): #401 code is for unauthorized. 403 for forbidden.
                self.is_connected = False
                self.error_occurred.emit("Home Assistant reachable but authentication failed.")
            else: #Any other response code (502 gateway, etc.) is treated as “not connected.”
                self.is_connected = False
                self.error_occurred.emit(f"Unexpected status: {response.status_code}")
                
        except requests.exceptions.Timeout as e:
            self.is_connected = False
            self.error_occurred.emit("Connection timed out.")
        except requests.exceptions.ConnectionError as e:
            self.is_connected = False
            self.error_occurred.emit("Cannot reach Home Assistant (network error).")
        except Exception as e:
            self.is_connected = False
            self.error_occurred.emit(f"Connection error: {e}")
        
        if was_connected != self.is_connected: #If the connection state changed (from True→False or False→True), it emits connection_status_changed with the new boolean.
            self.connection_status_changed.emit(self.is_connected)

    def _start_websocket(self):
        """Start WebSocket connection for real-time updates without blocking the UI thread."""
        if not self.use_websocket:
            return

        def run_websocket_loop():
            try:
                # Run the websocket loop in its own asyncio event loop on a background thread
                asyncio.run(self._websocket_loop())
            except Exception as e:
                logger.error(f"Failed to start WebSocket: {e}")
                try:
                    self.error_occurred.emit(f"WebSocket error: {str(e)}")
                except Exception:
                    pass

        #Spawns a daemon background thread named "HA-WebSocket" inside which runs asyncio.run(self._websocket_loop()), so the websocket has its own event loop and doesn’t block the UI thread.
        self.websocket_thread = threading.Thread(target=run_websocket_loop, name="HA-WebSocket", daemon=True)
        self.websocket_thread.start()

    async def _websocket_supervisor(self):
        """Reconnect loop with backoff; restarts _websocket_loop() on failures."""
        backoff = 1.0
        while True:
            try:
                await self._websocket_loop()
                backoff = 1.0  # reset if a full session ends cleanly (rare)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"WebSocket disconnected: {e}. Reconnecting in {backoff:.1f}s…")
                try:
                    self.error_occurred.emit(f"WebSocket disconnected, retrying… ({e})")
                except Exception:
                    pass
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)  # cap at 30s

    async def _websocket_loop(self):
        """WebSocket event loop for real-time updates."""
        # Builds ws_url by swapping http(s) → ws(s) and appending /api/websocket
        ws_url = self.host.replace('http', 'ws') + '/api/websocket'
        
        try:
            #async with websockets.connect(ws_url) opens the HA WS API.
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as websocket:
                self.websocket = websocket
                
                # Authenticate: Sends auth right away: {"type":"auth","access_token": <token>}.
                # Expect auth_required
                hello = json.loads(await websocket.recv())
                if hello.get("type") != "auth_required":
                    raise RuntimeError(f"Unexpected handshake: {hello}")
                # Create auth message
                auth_msg = {
                    "type": "auth",
                    "access_token": self.token
                }
                # Send token for authentication.
                await websocket.send(json.dumps(auth_msg))
                
                # Subscribe to state changes (events with id '1')
                subscribe_msg = {
                    "id": 1,
                    "type": "subscribe_events",
                    "event_type": "state_changed"
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                # Listen for messages: Asynchronously iterates incoming messages
                async for message in websocket:
                    try:
                        #Parses messages into JSON.
                        data = json.loads(message)
                        if data.get("type") == "event" and data.get("event", {}).get("event_type") == "state_changed":
                            event_data = data["event"]["data"]
                            entity_data = {
                                "entity_id": event_data["entity_id"],
                                "state": event_data["new_state"]["state"],
                                "attributes": event_data["new_state"].get("attributes", {}),
                                "last_changed": event_data["new_state"].get("last_changed"),
                                "last_updated": event_data["new_state"].get("last_updated")
                            }
                            self.entity_updated.emit(entity_data)
                    except Exception as e:
                        logger.error(f"Error processing WebSocket message: {e}")
                        
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            self.error_occurred.emit(f"WebSocket connection failed: {str(e)}")

    # For the functions below: the '-> ...' tells readers/tools what type the function is expected to return (here: a Dict or None).
    # It doesn’t change runtime behavior—it's just a hint for you, your IDE, and type checkers.
    # Optional[X] means the function can return either an X or None.

    def get_states(self) -> List[Dict]:
        """Fetch all entity states from Home Assistant. (GET)"""
        try:
            url = f"{self.host}/api/states"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status() #If the HTTP status is 4xx or 5xx, it raises requests.exceptions.HTTPError (a subclass of RequestException). ELSE If it’s 2xx or 3xx, it does nothing and execution continues.
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching states: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return []
        except Exception as e:
            error_msg = f"Unexpected error fetching states: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return []

    def get_entity_state(self, entity_id: str) -> Optional[Dict]:
        """Get state of a specific entity. (GET)"""
        try:
            url = f"{self.host}/api/states/{entity_id}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status() #If the HTTP status is 4xx or 5xx, it raises requests.exceptions.HTTPError (a subclass of RequestException). ELSE If it’s 2xx or 3xx, it does nothing and execution continues.
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching entity {entity_id}: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error fetching entity {entity_id}: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def call_service(self, domain: str, service: str, data: Dict = None) -> Optional[Dict]:
        """Call a Home Assistant service (e.g., turn_on light). (POST)"""
        try:
            url = f"{self.host}/api/services/{domain}/{service}"
            payload = data or {}
            response = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            response.raise_for_status() #If the HTTP status is 4xx or 5xx, it raises requests.exceptions.HTTPError (a subclass of RequestException). ELSE If it’s 2xx or 3xx, it does nothing and execution continues.
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Error calling service {domain}.{service}: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error calling service {domain}.{service}: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def get_config(self) -> Optional[Dict]:
        """Get Home Assistant configuration. (GET)"""
        try:
            url = f"{self.host}/api/config"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status() #If the HTTP status is 4xx or 5xx, it raises requests.exceptions.HTTPError (a subclass of RequestException). ELSE If it’s 2xx or 3xx, it does nothing and execution continues.
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching config: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error fetching config: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def get_automations(self) -> List[Dict]:
        """Get all automations by filtering /api/states."""
        try:
            url = f"{self.host}/api/states"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status() #If the HTTP status is 4xx or 5xx, it raises requests.exceptions.HTTPError (a subclass of RequestException). ELSE If it’s 2xx or 3xx, it does nothing and execution continues.
            entities = response.json()
            automations = [e for e in entities if e.get("entity_id", "").startswith("automation.")]
            return automations
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching automations: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return []
        except Exception as e:
            error_msg = f"Unexpected error fetching automations: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return []

    def create_automation(self, automation_data: Dict) -> Optional[Dict]:
        """Create a new automation. (POST)"""
        try:
            url = f"{self.host}/api/config/automation/config"
            response = requests.post(url, headers=self.headers, json=automation_data, timeout=self.timeout)
            response.raise_for_status() #If the HTTP status is 4xx or 5xx, it raises requests.exceptions.HTTPError (a subclass of RequestException). ELSE If it’s 2xx or 3xx, it does nothing and execution continues.
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"Error creating automation: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error creating automation: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def toggle_entity(self, entity_id: str) -> bool:
        """Toggle an entity (on/off)."""
        domain = entity_id.split('.')[0]
        result = self.call_service(domain, "toggle", {"entity_id": entity_id})
        return result is not None

    def turn_on_entity(self, entity_id: str, **kwargs) -> bool:
        """Turn on an entity."""
        domain = entity_id.split('.')[0]
        data = {"entity_id": entity_id}
        data.update(kwargs)
        result = self.call_service(domain, "turn_on", data)
        return result is not None

    def turn_off_entity(self, entity_id: str) -> bool:
        """Turn off an entity."""
        domain = entity_id.split('.')[0]
        result = self.call_service(domain, "turn_off", {"entity_id": entity_id})
        return result is not None

    def close(self):
        """Close connections and cleanup."""
        if self.websocket_task:
            self.websocket_task.cancel()
        if self.connection_timer:
            self.connection_timer.stop()