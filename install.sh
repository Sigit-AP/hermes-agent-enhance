#!/usr/bin/env bash
# =============================================================================
# Hermes Agent Enhance — Tier-3 Resilient Multi-Python Installer
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

# 1. Update and ensure Python 3.11+ is installed
if command -v apt-get >/dev/null 2>&1; then
    run_privileged apt-get update -y
    run_privileged apt-get install -y software-properties-common git curl sqlite3 libffi-dev libssl-dev ripgrep nodejs npm build-essential || true
    
    # Check if existing python3 is < 3.11 (e.g. Ubuntu 22.04 LTS which ships with 3.10)
    NEED_PYTHON_PPA=false
    if ! command -v python3.11 >/dev/null 2>&1 && ! command -v python3.12 >/dev/null 2>&1; then
        PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
        if [ "$(echo "$PY_VER < 3.11" | awk -F. '{if ($1 < 3 || ($1 == 3 && $2 < 11)) print 1; else print 0}')" -eq 1 ]; then
            NEED_PYTHON_PPA=true
        fi
    fi

    if [ "$NEED_PYTHON_PPA" = true ]; then
        echo "Detected Python < 3.11. Adding deadsnakes PPA to install Python 3.11..."
        run_privileged add-apt-repository -y ppa:deadsnakes/ppa || true
        run_privileged apt-get update -y || true
        run_privileged apt-get install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils || true
    fi

elif command -v dnf >/dev/null 2>&1; then
    run_privileged dnf install -y python3.11 python3.11-devel python3.11-pip gcc git curl sqlite sqlite-devel ripgrep nodejs npm || run_privileged dnf install -y python3 python3-devel python3-pip gcc git curl sqlite sqlite-devel ripgrep nodejs npm || true
elif command -v yum >/dev/null 2>&1; then
    run_privileged yum install -y python3.11 python3.11-devel gcc git curl sqlite sqlite-devel ripgrep nodejs npm || run_privileged yum install -y python3 python3-devel python3-pip gcc git curl sqlite sqlite-devel ripgrep nodejs npm || true
elif command -v apk >/dev/null 2>&1; then
    run_privileged apk add python3 py3-pip python3-dev gcc musl-dev git curl sqlite sqlite-dev ripgrep nodejs npm bash || true
elif command -v pacman >/dev/null 2>&1; then
    run_privileged pacman -Sy --noconfirm python python-pip base-devel git curl sqlite ripgrep nodejs npm || true
fi

# Detect best available Python 3.11+ binary
PY_BIN=""
for candidate in python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        IS_VALID=$("$candidate" -c 'import sys; print(1 if sys.version_info >= (3, 11) else 0)' 2>/dev/null || echo "0")
        if [ "$IS_VALID" -eq 1 ]; then
            PY_BIN="$candidate"
            break
        fi
    fi
done

if [ -z "$PY_BIN" ]; then
    echo "Error: Python 3.11 or higher is required to run Hermes Agent."
    echo "Current system python3 version: $(python3 --version 2>&1 || echo 'none')"
    echo "Please install Python 3.11 manually (e.g. apt install python3.11 python3.11-venv)."
    exit 1
fi

echo "Using Python binary: $($PY_BIN --version) ($PY_BIN)"

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

# 3. Virtual Environment with selected Python 3.11+
if [ -d "$INSTALL_DIR/venv" ]; then
    # Verify if existing venv uses >= 3.11
    VENV_VALID=$("$INSTALL_DIR/venv/bin/python" -c 'import sys; print(1 if sys.version_info >= (3, 11) else 0)' 2>/dev/null || echo "0")
    if [ "$VENV_VALID" -ne 1 ]; then
        echo "Recreating venv with $PY_BIN..."
        rm -rf "$INSTALL_DIR/venv"
        "$PY_BIN" -m venv "$INSTALL_DIR/venv"
    fi
else
    "$PY_BIN" -m venv "$INSTALL_DIR/venv"
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
