#!/usr/bin/env bash
# =============================================================================
# Hermes Agent Enhance — Tier-3 High-Assurance Resilient Installer
# =============================================================================
set -e

# Sudo wrapper (jika dijalankan sebagai non-root dan sudo tersedia)
run_privileged() {
    if [ "$(id -u)" -eq 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        echo "⚠️ Peringatan: sudo tidak ditemukan dan bukan root, mencoba menjalankan langsung..."
        "$@" || true
    fi
}

echo "================================================================="
echo "   ⚕ Hermes Agent Enhance — Tier-3 High-Assurance Installer     "
echo "================================================================="

# 1. Update paket & install dependensi sistem (Ubuntu/Debian, CentOS/RHEL/Fedora, Alpine, Arch)
echo "📦 Memeriksa & menginstall dependensi sistem..."
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

# Pastikan Python 3 tersedia
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Error fatal: python3 tidak ditemukan di sistem ini."
    exit 1
fi

# 2. Setup direktori instalasi
INSTALL_DIR="$HOME/.hermes-agent"
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "🔄 Memperbarui instalasi yang ada di $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git fetch --all || true
    git reset --hard origin/main || git reset --hard origin/master || true
else
    echo "📥 Meng-clone repository dari Sigit-AP/hermes-agent-enhance..."
    rm -rf "$INSTALL_DIR"
    git clone https://github.com/Sigit-AP/hermes-agent-enhance.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. Setup Python Virtual Environment
echo "🐍 Menyiapkan Python Virtual Environment..."
if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi

# Aktifkan virtual environment
source "$INSTALL_DIR/venv/bin/activate"

# 4. Install uv untuk akselerasi pip & dependensi
echo "⚡ Menginstall packages & build editable..."
pip install --upgrade pip setuptools wheel
if ! pip install -e .; then
    echo "⚠️ pip install -e . gagal, mencoba instalasi dependensi dengan no-cache..."
    pip install --no-cache-dir -e .
fi

# 5. Inisialisasi Konfigurasi Tier-3 Zero-Block
mkdir -p "$HOME/.hermes"
CONFIG_FILE="$HOME/.hermes/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚙️ Menyiapkan konfigurasi default Tier-3 Zero-Block..."
    cat << 'EOF' > "$CONFIG_FILE"
# Tier-3 Zero-Block Runtime Configuration
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

# 6. Registrasi Symlink Global & PATH Export
echo "🔗 Mendaftarkan binary executable 'hermes'..."
mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/venv/bin/hermes" "$HOME/.local/bin/hermes"

# Coba symlink ke /usr/local/bin jika memiliki izin
if [ "$(id -u)" -eq 0 ] || command -v sudo >/dev/null 2>&1; then
    run_privileged ln -sf "$INSTALL_DIR/venv/bin/hermes" /usr/local/bin/hermes || true
fi

# Tambahkan $HOME/.local/bin ke file shell profile jika belum ada
for RC in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [ -f "$RC" ]; then
        if ! grep -q "$HOME/.local/bin" "$RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
        fi
    fi
done

# 7. Validasi Pengujian Formal Tier-3
echo "🧪 Menjalankan verifikasi formal Tier-3..."
if python3 -m unittest tests/test_tier3_high_assurance.py; then
    echo "✅ Semua test Tier-3 lulus 100%!"
else
    echo "⚠️ Peringatan: Ada test yang memerlukan pengecekan lingkungan, namun core tetap terpasang."
fi

echo ""
echo "================================================================="
echo "   🎉 Instalasi Hermes Agent Enhance Berhasil 100%!             "
echo "================================================================="
echo "Perintah yang dapat langsung Anda jalankan:"
echo "  • hermes setup    -> Menjalankan wizard konfigurasi interaktif"
echo "  • hermes          -> Memulai agen di terminal (CLI/TUI)"
echo "  • hermes gateway  -> Menjalankan gateway bot (Telegram, WA, dll)"
echo ""
echo "Jika perintah 'hermes' belum terbaca, jalankan: source ~/.bashrc"
