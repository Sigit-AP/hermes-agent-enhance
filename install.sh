#!/usr/bin/env bash
set -e

echo "=== Memulai Instalasi Hermes Agent Enhance (Tier-3 High-Assurance) ==="

# 1. Update sistem & dependensi dasar
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv git curl sqlite3
elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y python3 python3-pip git curl sqlite
fi

# 2. Setup direktori instalasi
INSTALL_DIR="$HOME/.hermes-agent"
if [ -d "$INSTALL_DIR" ]; then
    echo "Direktori lama ditemukan, memperbarui codebase..."
    cd "$INSTALL_DIR"
    git pull origin main || git pull origin master || true
else
    echo "Cloning repository dari Sigit-AP/hermes-agent-enhance..."
    git clone https://github.com/Sigit-AP/hermes-agent-enhance.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. Setup Python Virtual Environment
echo "Membuat Virtual Environment..."
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"

# 4. Install dependensi & paket editable
echo "Menginstall packages..."
pip install --upgrade pip
pip install -e .

# 5. Setup default Zero-Block Config
mkdir -p "$HOME/.hermes"
if [ ! -f "$HOME/.hermes/config.yaml" ]; then
    echo "Membuat konfigurasi default Tier-3 Zero-Block..."
    cat << 'EOF' > "$HOME/.hermes/config.yaml"
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

# 6. Buat shortcut binary global
echo "Membuat symlink executable ke /usr/local/bin/hermes..."
sudo ln -sf "$INSTALL_DIR/venv/bin/hermes" /usr/local/bin/hermes

# 7. Jalankan test validasi Tier-3
echo "Menjalankan uji validasi Tier-3..."
python3 -m unittest tests/test_tier3_high_assurance.py

echo ""
echo "=== Instalasi Selesai 100% ==="
echo "Jalankan 'hermes' dari terminal mana saja untuk memulai, atau 'hermes setup' untuk konfigurasi."
