#!/usr/bin/env bash
set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_PATH="$REPO_DIR/bin/skill-hub"

echo "=========================================================="
echo "   Installing skill-hub (Universal Multi-Agent Hub)"
echo "=========================================================="

# 1. Detect Python 3
PYTHON_BIN=""
if command -v /opt/homebrew/bin/python3 >/dev/null 2>&1; then
    PYTHON_BIN="/opt/homebrew/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "Error: python3 is required but not found."
    exit 1
fi
echo "✓ Python: $($PYTHON_BIN --version) ($PYTHON_BIN)"

# 2. Make executable
chmod +x "$BIN_PATH"

# 3. Determine target bin directory
TARGET_DIR=""
if [ -d "$HOME/.local/bin" ] && [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
    TARGET_DIR="$HOME/.local/bin"
elif [ -w "/opt/homebrew/bin" ]; then
    TARGET_DIR="/opt/homebrew/bin"
elif [ -w "/usr/local/bin" ]; then
    TARGET_DIR="/usr/local/bin"
else
    mkdir -p "$HOME/.local/bin"
    TARGET_DIR="$HOME/.local/bin"
fi

TARGET_BIN="$TARGET_DIR/skill-hub"
ln -sf "$BIN_PATH" "$TARGET_BIN"
echo "✓ Installed executable link: ${TARGET_BIN/#$HOME/~}"

# Check PATH
if [[ ":$PATH:" != *":$TARGET_DIR:"* ]]; then
    echo ""
    echo "Notice: $TARGET_DIR is not yet in your PATH."
    echo "Add the following line to your ~/.zshrc or ~/.bashrc:"
    echo "    export PATH=\"$TARGET_DIR:\$PATH\""
    echo ""
fi

# 4. Run doctor
echo ""
"$TARGET_BIN" doctor

echo ""
echo "=========================================================="
echo "   Installation Complete!"
echo "   Try running:"
echo "       skill-hub doctor"
echo "       skill-hub import --from agy    # Share existing skills"
echo "       skill-hub sync                 # Sync to all agents"
echo "       skill-hub install <source>     # Install new skill/plugin"
echo "=========================================================="
