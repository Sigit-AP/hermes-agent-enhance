#!/usr/bin/env bash
# =============================================================================
# Hermes Agent Enhance — Grouped Installer & Clean-Purge Utility
# =============================================================================
set -e

# Non-interactive mode for apt / dpkg (Suppress all dialogs & automatic defaults)
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=l
export UCF_FORCE_CONFFOLD=1

INSTALL_DIR="$HOME/.hermes-agent"
CONFIG_DIR="$HOME/.hermes"
LOCAL_BIN="$HOME/.local/bin/hermes"
SYS_BIN="/usr/local/bin/hermes"

# -----------------------------------------------------------------------------
# Privilege Helper
# -----------------------------------------------------------------------------
run_privileged() {
    if [ "$(id -u)" -eq 0 ]; then
        DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l "$@"
    else
        "$@" || true
    fi
}

# Silence needrestart completely if present on Ubuntu/Debian systems
if [ -f /etc/needrestart/needrestart.conf ]; then
    run_privileged sed -i "s/#\$nrconf{restart} = 'i';/\$nrconf{restart} = 'l';/g" /etc/needrestart/needrestart.conf 2>/dev/null || true
    run_privileged sed -i "s/\$nrconf{restart} = 'i';/\$nrconf{restart} = 'l';/g" /etc/needrestart/needrestart.conf 2>/dev/null || true
    run_privileged sed -i "s/#\$nrconf{kernelhints} = -1;/\$nrconf{kernelhints} = 0;/g" /etc/needrestart/needrestart.conf 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# Clean / Purge Functionality
# -----------------------------------------------------------------------------
purge_all() {
    echo "========================================================"
    echo "   Cleaning and purging all Hermes Agent installations  "
    echo "========================================================"
    
    echo "[-] Removing installation directory: $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
    
    echo "[-] Removing user configuration directory: $CONFIG_DIR"
    rm -rf "$CONFIG_DIR"
    
    echo "[-] Removing local binary symlink: $LOCAL_BIN"
    rm -f "$LOCAL_BIN"
    
    if [ "$(id -u)" -eq 0 ] || command -v sudo >/dev/null 2>&1; then
        echo "[-] Removing system binary symlink: $SYS_BIN"
        run_privileged rm -f "$SYS_BIN" || true
    fi

    echo ""
    echo "Cleanup complete. The system is clean."
    exit 0
}

# Check if user requested clean / uninstall
if [ "$1" = "--clean" ] || [ "$1" = "clean" ] || [ "$1" = "uninstall" ] || [ "$1" = "--uninstall" ]; then
    purge_all
fi

# -----------------------------------------------------------------------------
# Trap on Failure
# -----------------------------------------------------------------------------
trap 'catch_failure $? $LINENO' ERR
catch_failure() {
    local exit_code=$1
    local line_no=$2
    echo ""
    echo "========================================================"
    echo "❌ Installation interrupted at Group stage (Line $line_no) with error code $exit_code."
    echo "To completely wipe all partial files and start fresh, run:"
    echo "   bash <(curl -fsSL https://raw.githubusercontent.com/Sigit-AP/hermes-agent-enhance/main/install.sh) --clean"
    echo "========================================================"
    exit "$exit_code"
}

echo "========================================================"
echo "   Hermes Agent Enhance — Grouped Stage Installer       "
echo "========================================================"
echo "Total Stages: 5 Groups"
echo "  [Group 1/5] OS Base Tools & Build Headers"
echo "  [Group 2/5] Python 3.11+ Runtime Environment"
echo "  [Group 3/5] Repository Clone & Virtual Environment"
echo "  [Group 4/5] Package Dependencies & Core Installation"
echo "  [Group 5/5] Configuration, Binary Links & Test Verification"
echo "========================================================"
echo ""

# -----------------------------------------------------------------------------
# GROUP 1: OS Base Tools & Build Headers
# -----------------------------------------------------------------------------
echo "▶ [Group 1/5] Checking & Installing OS Toolchain..."
if command -v apt-get >/dev/null 2>&1; then
    run_privileged apt-get update -y
    run_privileged apt-get install -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" software-properties-common git curl sqlite3 libffi-dev libssl-dev ripgrep nodejs npm build-essential
elif command -v dnf >/dev/null 2>&1; then
    run_privileged dnf install -y gcc git curl sqlite sqlite-devel ripgrep nodejs npm make
elif command -v yum >/dev/null 2>&1; then
    run_privileged yum install -y gcc git curl sqlite sqlite-devel ripgrep nodejs npm make
elif command -v apk >/dev/null 2>&1; then
    run_privileged apk add gcc musl-dev git curl sqlite sqlite-dev ripgrep nodejs npm bash make
elif command -v pacman >/dev/null 2>&1; then
    run_privileged pacman -Sy --noconfirm base-devel git curl sqlite ripgrep nodejs npm
fi
echo "✔ [Group 1/5] OS Base Tools installed successfully."
echo ""

# -----------------------------------------------------------------------------
# GROUP 2: Python 3.11+ Runtime Environment
# -----------------------------------------------------------------------------
echo "▶ [Group 2/5] Checking Python 3.11+ Runtime..."
if command -v apt-get >/dev/null 2>&1; then
    NEED_PYTHON_PPA=false
    if ! command -v python3.11 >/dev/null 2>&1 && ! command -v python3.12 >/dev/null 2>&1; then
        PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
        if [ "$(echo "$PY_VER < 3.11" | awk -F. '{if ($1 < 3 || ($1 == 3 && $2 < 11)) print 1; else print 0}')" -eq 1 ]; then
            NEED_PYTHON_PPA=true
        fi
    fi

    if [ "$NEED_PYTHON_PPA" = true ]; then
        echo "  Adding deadsnakes PPA for Python 3.11..."
        run_privileged add-apt-repository -y ppa:deadsnakes/ppa || true
        run_privileged apt-get update -y || true
        run_privileged apt-get install -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" python3.11 python3.11-venv python3.11-dev python3.11-distutils
    fi
elif command -v dnf >/dev/null 2>&1; then
    run_privileged dnf install -y python3.11 python3.11-devel python3.11-pip || true
elif command -v yum >/dev/null 2>&1; then
    run_privileged yum install -y python3.11 python3.11-devel || true
fi

# Resolve Python Binary
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
    echo "❌ Error in Group 2: Python 3.11 or higher is required."
    exit 1
fi
echo "✔ [Group 2/5] Python runtime verified: $($PY_BIN --version) ($PY_BIN)"
echo ""

# -----------------------------------------------------------------------------
# GROUP 3: Repository Clone & Virtual Environment
# -----------------------------------------------------------------------------
echo "▶ [Group 3/5] Setting up Repository and Virtual Environment..."
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "  Updating repository in $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git fetch --all || true
    git reset --hard origin/main || git reset --hard origin/master || true
else
    echo "  Cloning from Sigit-AP/hermes-agent-enhance..."
    rm -rf "$INSTALL_DIR"
    git clone https://github.com/Sigit-AP/hermes-agent-enhance.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

if [ -d "$INSTALL_DIR/venv" ]; then
    VENV_VALID=$("$INSTALL_DIR/venv/bin/python" -c 'import sys; print(1 if sys.version_info >= (3, 11) else 0)' 2>/dev/null || echo "0")
    if [ "$VENV_VALID" -ne 1 ]; then
        echo "  Rebuilding virtual environment with $PY_BIN..."
        rm -rf "$INSTALL_DIR/venv"
        "$PY_BIN" -m venv "$INSTALL_DIR/venv"
    fi
else
    echo "  Creating virtual environment with $PY_BIN..."
    "$PY_BIN" -m venv "$INSTALL_DIR/venv"
fi

source "$INSTALL_DIR/venv/bin/activate"
echo "✔ [Group 3/5] Repository and virtual environment ready."
echo ""

# -----------------------------------------------------------------------------
# GROUP 4: Package Dependencies & Core Installation
# -----------------------------------------------------------------------------
echo "▶ [Group 4/5] Installing Dependencies and Hermes Core Package..."
pip install --upgrade pip setuptools wheel
pip install -e .
echo "✔ [Group 4/5] Package dependencies and editable package installed."
echo ""

# -----------------------------------------------------------------------------
# GROUP 5: Configuration, Binary Links & Test Verification
# -----------------------------------------------------------------------------
echo "▶ [Group 5/5] Finalizing Configuration & Binary Links..."
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    cat << 'EOF' > "$CONFIG_DIR/config.yaml"
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

mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/venv/bin/hermes" "$LOCAL_BIN"

if [ "$(id -u)" -eq 0 ] || command -v sudo >/dev/null 2>&1; then
    run_privileged ln -sf "$INSTALL_DIR/venv/bin/hermes" "$SYS_BIN" || true
fi

for RC in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [ -f "$RC" ]; then
        if ! grep -q "$HOME/.local/bin" "$RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
        fi
    fi
done

echo "  Running verification tests..."
python3 -m unittest tests/test_tier3_high_assurance.py

echo "✔ [Group 5/5] Configuration and verification complete."
echo ""

# -----------------------------------------------------------------------------
# Final Summary
# -----------------------------------------------------------------------------
echo "========================================================"
echo "Installation complete."
echo "Stages summary:"
echo "  [Group 1/5] OS Base Tools ................. [DONE]"
echo "  [Group 2/5] Python 3.11+ Runtime .......... [DONE]"
echo "  [Group 3/5] Repository & Venv ............. [DONE]"
echo "  [Group 4/5] Dependencies & Package ........ [DONE]"
echo "  [Group 5/5] Config, Links & Tests ......... [DONE]"
echo "========================================================"
echo "Commands:"
echo "  hermes setup"
echo "  hermes"
echo "  hermes gateway"
echo ""
echo "Purge/Uninstall shortcut (if ever needed):"
echo "  bash <(curl -fsSL https://raw.githubusercontent.com/Sigit-AP/hermes-agent-enhance/main/install.sh) --clean"
echo "========================================================"
