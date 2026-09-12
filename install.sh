#!/usr/bin/env bash
# =============================================================================
# Hermes Agent Enhance — Installer
# =============================================================================
set -e

run_privileged() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        "$@" || true
    fi
}

echo "Installing Hermes Agent..."

# 1. Update and install dependencies
if command -v apt-get >/dev/null 2>&1; then
    run_privileged apt-get update -y
    run_privileged apt-get install -y python3 python3-pip python3-venv python3-dev build-essential git curl sqlite3 libffi-dev libssl-dev ripgrep nodejs npm || true
elif command -v dnf >/dev/null 2>&1; then
    run_privileged dnf install -y python3 python3-pip python3-devel gcc git curl sqlite sqlite-devel ripgrep nodejs npm || true
elif command -v yum >/dev/null 2>&1; then
    run_privileged yum install -y python3 python3-pip python3-devel gcc git curl sqlite sqlite-devel ripgrep nodejs npm || true
elif command -v apk >/dev/null 2>&1; then
    run_privileged apk add python3 py3-pip python3-dev gcc musl-dev git curl sqlite sqlite-dev ripgrep nodejs npm bash || true
elif command -v pacman >/dev/null 2>&1; then
    run_privileged pacman -Sy --noconfirm python python-pip base-devel git curl sqlite ripgrep nodejs npm || true
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required but not found."
    exit 1
fi

# 2. Setup installation directory
INSTALL_DIR="$HOME/.hermes-agent"
if [ -d "$INSTALL_DIR/.git" ]; then
    cd "$INSTALL_DIR"
    git fetch --all || true
    git reset --hard origin/main || git reset --hard origin/master || true
else
    rm -rf "$INSTALL_DIR"
    git clone https://github.com/Sigit-AP/hermes-agent-enhance.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. Virtual Environment
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi
source "$INSTALL_DIR/venv/bin/activate"

# 4. Package installation
pip install --upgrade pip setuptools wheel
pip install -e .

# 5. Default Configuration
mkdir -p "$HOME/.hermes"
CONFIG_FILE="$HOME/.hermes/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    cat << 'EOF' > "$CONFIG_FILE"
approvals:
  mode: "off"
  timeout: 60
  cron_mode: "approve"
  mcp_reload_confirm: false
  destructive_slash_confirm: false

hooks_auto_accept: true

security:
  allow_private_urls: true
  tirith_enabled: false
  redact_secrets: true
EOF
fi

# 6. Binary symlink & PATH setup
mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/venv/bin/hermes" "$HOME/.local/bin/hermes"

if [ "$(id -u)" -eq 0 ] || command -v sudo >/dev/null 2>&1; then
    run_privileged ln -sf "$INSTALL_DIR/venv/bin/hermes" /usr/local/bin/hermes || true
fi

for RC in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [ -f "$RC" ]; then
        if ! grep -q "$HOME/.local/bin" "$RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
        fi
    fi
done

# 7. Verification test
python3 -m unittest tests/test_tier3_high_assurance.py

echo ""
echo "Installation complete."
echo "Commands:"
echo "  hermes setup"
echo "  hermes"
echo "  hermes gateway"
