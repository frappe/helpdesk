#!/bin/bash
# Login Rollback Script - Sprint 8
# Restores previous /login implementation from backup

set -e

WWW_DIR="/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/www"

if [ -z "$1" ]; then
    echo "❌ Error: Backup directory not specified"
    echo "Usage: ./rollback-login.sh <backup-directory>"
    echo ""
    echo "Available backups:"
    ls -1 /home/ubuntu/frappe-bench/apps/helpdesk/backups/ 2>/dev/null || echo "  (none)"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "${BACKUP_DIR}" ]; then
    echo "❌ Error: Backup directory does not exist: ${BACKUP_DIR}"
    exit 1
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Helpdesk Login - Rollback                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Confirmation prompt
read -p "⚠️  This will restore the login page from backup. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Rollback cancelled"
    exit 1
fi

echo "🔄 Restoring from backup..."

# Restore files
if [ -f "${BACKUP_DIR}/login.py.bak" ]; then
    cp "${BACKUP_DIR}/login.py.bak" "${WWW_DIR}/login.py"
    echo "   ✓ Restored login.py"
fi

if [ -f "${BACKUP_DIR}/login.html.bak" ]; then
    cp "${BACKUP_DIR}/login.html.bak" "${WWW_DIR}/login.html"
    echo "   ✓ Restored login.html"
fi

echo ""
echo "🔨 Rebuilding assets..."
cd /home/ubuntu/frappe-bench
bench build --app helpdesk

echo ""
echo "🗑️  Clearing cache..."
bench clear-cache

echo ""
echo "🔄 Restarting services..."
bench restart

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Rollback complete!"
echo ""
echo "🌐 Check: http://localhost:8000/login"
echo "📄 Backup preserved at: ${BACKUP_DIR}"
echo "════════════════════════════════════════════════════════════"
