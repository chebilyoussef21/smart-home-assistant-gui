# config/settings.py

# host = 'localhost'
host = '10.0.0.48'

HOME_ASSISTANT = {
    #"host": "http://localhost:8123",  # or use Pi IP like "http://192.168.1.50:8123"
    "host": f"http://{host}:8123",
    "api_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzN2Y1ZDE5Y2YwMDA0YTQwOGE0NWM0NGE2NGNjZTViZiIsImlhdCI6MTc1NzY0MDIzOCwiZXhwIjoyMDczMDAwMjM4fQ.wdn7G6yv-ICWpb6GK9JzDUBjfAyFzLcEvefTcgllCaA",  # generate from HA user profile
    "use_websocket": True,
    "timeout": 10  # seconds
}

UI = {
    "theme": "dark",
    "refresh_interval": 5,  # seconds
}