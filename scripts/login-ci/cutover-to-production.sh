#!/bin/bash
# Production Cutover Script - Sprint 8
# Replaces /login with redesigned login page

set -e

APP_DIR="/home/ubuntu/frappe-bench/apps/helpdesk"
WWW_DIR="${APP_DIR}/helpdesk/www"
BACKUP_DIR="${APP_DIR}/backups/login-$(date +%Y%m%d_%H%M%S)"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Helpdesk Login - Production Cutover                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Confirmation prompt
read -p "⚠️  This will replace the production /login route. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "❌ Cutover cancelled"
    exit 1
fi

echo "📦 Creating backup..."
mkdir -p "${BACKUP_DIR}"

# Backup existing login files (if they exist)
if [ -f "${WWW_DIR}/login.py" ]; then
    cp "${WWW_DIR}/login.py" "${BACKUP_DIR}/login.py.bak"
    echo "   ✓ Backed up login.py"
fi

if [ -f "${WWW_DIR}/login.html" ]; then
    cp "${WWW_DIR}/login.html" "${BACKUP_DIR}/login.html.bak"
    echo "   ✓ Backed up login.html"
fi

echo ""
echo "🔄 Performing cutover..."

# Copy login_preview files to login
cp "${WWW_DIR}/login_preview.py" "${WWW_DIR}/login.py"
cp "${WWW_DIR}/login_preview.html" "${WWW_DIR}/login.html"

echo "   ✓ Copied login_preview.py → login.py"
echo "   ✓ Copied login_preview.html → login.html"

echo ""
echo "🔧 Removing role gate..."

# Remove role gate from login.py (allow Guest access)
sed -i '/# Role gate: System Manager or HD Admin only/,/frappe.throw(_("Not Found"), frappe.DoesNotExistError)/d' "${WWW_DIR}/login.py"

# Remove preview_mode flag
sed -i 's/"preview_mode": True,/"preview_mode": False,/g' "${WWW_DIR}/login.py"

echo "   ✓ Role gate removed"
echo "   ✓ Preview mode disabled"

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
echo "✅ Cutover complete!"
echo ""
echo "📄 Backup location: ${BACKUP_DIR}"
echo "🌐 Production URL: http://localhost:8000/login"
echo ""
echo "⚠️  Next steps:"
echo "   1. Test /login route (anonymous access)"
echo "   2. Monitor error logs: tail -f sites/logs/error.log"
echo "   3. Collect user feedback"
echo "   4. Keep backup for 30 days"
echo ""
echo "📋 Rollback command (if needed):"
echo "   ./rollback-login.sh ${BACKUP_DIR}"
echo "════════════════════════════════════════════════════════════"
