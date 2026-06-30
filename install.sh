#!/bin/bash
# Afia Clinic - Smart Linux/Mac Installer
# Supports: Docker or Native Odoo 18 CE
# Usage: bash install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULES_DIR="$SCRIPT_DIR/modules"

echo ""
echo "  Afia Clinic - Installer"
echo "  ITCS (IT Corner Solutions) - itcornersolutions.net"
echo ""

# ── Detect Docker ─────────────────────────────────────────────────────────────
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    echo "  [DETECTED] Docker available - using Docker install"
    echo ""
    cd "$SCRIPT_DIR/docker"
    docker compose up -d
    echo ""
    echo "  Waiting for Odoo to start (30 seconds)..."
    sleep 30
    echo ""
    echo "  Done! Open your browser:"
    echo "  http://localhost:8069"
    echo ""
    echo "  Create a new database, go to Apps and install 'Dental Hospital'."
    echo "  All 38 Afia Clinic modules will be available."

# ── Detect Native Odoo (Linux) ────────────────────────────────────────────────
elif [ -d "/usr/lib/python3/dist-packages/odoo" ] || [ -d "/opt/odoo" ]; then
    # Find custom_addons path
    ADDONS_PATH=""
    for p in "/opt/odoo/custom_addons" "/usr/lib/python3/dist-packages/odoo/custom_addons" "/opt/odoo18/custom_addons"; do
        if [ -d "$p" ]; then ADDONS_PATH="$p"; break; fi
    done
    if [ -z "$ADDONS_PATH" ]; then
        mkdir -p /opt/odoo/custom_addons
        ADDONS_PATH="/opt/odoo/custom_addons"
    fi

    echo "  [DETECTED] Odoo installation found"
    echo "  Copying modules to: $ADDONS_PATH"
    cp -r "$MODULES_DIR"/. "$ADDONS_PATH/"
    echo "  Copied $(ls "$MODULES_DIR" | wc -l) modules"

    # Restart
    if systemctl is-active --quiet odoo; then
        echo "  Restarting Odoo service..."
        sudo systemctl restart odoo
        sleep 15
    fi

    echo ""
    echo "  Done! Open your browser:"
    echo "  http://localhost:8069"
    echo ""
    echo "  Go to Apps > Update Apps List, then install 'Dental Hospital'."

else
    echo "  [NOT FOUND] Neither Docker nor Odoo 18 detected."
    echo ""
    echo "  Option A (Recommended): Install Docker"
    echo "    Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
    echo "    Mac:           https://docker.com/products/docker-desktop"
    echo "    Then re-run:   bash install.sh"
    echo ""
    echo "  Option B: Install Odoo 18 CE"
    echo "    https://www.odoo.com/page/download"
    echo "    Then re-run:   bash install.sh"
fi

echo ""
