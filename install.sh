#!/usr/bin/env bash
# This script:
# - installs Docker if missing,
# - sets up /opt/customHAapp on the target machine,
# - drops a systemd unit so it starts at boot,
# - uses the docker compose file you commit here.
# Usage on a new machine: curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/main/install.sh | sudo bash

set -euo pipefail

APP_DIR="/opt/customHAapp"

# 1) Install Docker if needed (Linux)
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  # add calling user to docker group for convenience
  if [[ -n "${SUDO_USER-}" ]]; then
    usermod -aG docker "$SUDO_USER" || true
  fi
fi

# 2) Ensure compose plugin
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin missing. Install Docker Desktop or Compose plugin."
  exit 1
fi

# 3) Install app files (pull from your GitHub repo raw)
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Fetch docker-compose.yml from your main branch
curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/main/docker-compose.yml -o docker-compose.yml

# 4) Allow X11 (Linux desktops only; safe to try)
if command -v xhost >/dev/null 2>&1; then
  xhost +local:docker || true
fi

# 5) Create systemd unit
cat > /etc/systemd/system/customHAapp.service <<'UNIT'
[Unit]
Description=customHAapp (docker compose)
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/opt/customHAapp
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
RemainAfterExit=true
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now customHAapp.service

echo "Installed. If this is a desktop Linux machine, log out/in once so your user gets docker group perms."
