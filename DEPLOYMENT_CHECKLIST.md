# Email Account Selection Feature - Deployment Checklist

## Feature Overview
Users can select which email account to send from when replying to HD Tickets.

## Components Required

### 1. Frontend (EmailEditor.vue)
✅ **Status**: Already correct locally and on production
- Has `FROM:` field with `SingleSelectEmailInput`
- Passes `email_account` parameter to backend

### 2. Backend (hd_ticket.py)
✅ **Status**: Code exists on GitHub, needs verification on production
- Method signature: `reply_via_agent(..., email_account: str = None)`
- Handles `email_account` parameter correctly

## Production Deployment Steps

### Step 1: Verify Backend Code on Production

```bash
# On production server
cd apps/helpdesk

# Check current branch
git branch
# Should be: feature/email-transfer-and-order-history

# Check remote
git remote -v
# Should point to your fork

# Pull latest code
git pull origin feature/email-transfer-and-order-history

# VERIFY the parameter exists
grep -A 8 "def reply_via_agent" helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py | grep email_account
# Should show: email_account: str = None,
```

### Step 2: Clear Python Caches

```bash
cd apps/helpdesk

# Delete all Python bytecode
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -name "*.pyo" -delete

# Clear site-level caches
cd ../..
find sites -name "*.pyc" -delete 2>/dev/null || true
find sites -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
```

### Step 3: Rebuild Frontend

```bash
bench build --app helpdesk
```

### Step 4: Clear Frappe Cache

```bash
bench --site <your-site> clear-cache
bench --site <your-site> clear-website-cache
```

### Step 5: Restart Services

```bash
# Stop all processes
bench restart --force-stop

# Start fresh
bench restart
```

### Step 6: Verify Backend Method Signature

```bash
bench --site <your-site> console
```

Then run:
```python
import inspect
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket
sig = inspect.signature(HDTicket.reply_via_agent)
print(sig)
```

**Expected output:**
```
(self, message: str, to: str = None, cc: str = None, bcc: str = None, attachments: List[str] = [], email_account: str = None)
```

If `email_account` is missing, the backend code is not updated.

## Troubleshooting

### Error: "email_account parameter not found"
- Backend file doesn't have the parameter
- Solution: Pull latest code from GitHub branch

### Error: "email_account parameter exists but still getting error"
- Python is using cached bytecode
- Solution: Clear all `.pyc` files and restart

### Frontend shows FROM field but backend rejects it
- Frontend updated, backend not updated
- Solution: Update backend code and clear caches

## Verification Test

1. Open an HD Ticket
2. Click "Reply"
3. Check if "FROM:" field appears at top
4. Select an email account from dropdown
5. Compose and send email
6. Should work without errors

## Files Modified

1. **Frontend**: `apps/helpdesk/desk/src/components/EmailEditor.vue`
   - Added `SingleSelectEmailInput` component
   - Added `fromEmailAccount` ref
   - Passes `email_account` in API call

2. **Backend**: `apps/helpdesk/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`
   - Added `email_account: str = None` parameter
   - Handles email account selection logic

## Git Status Check

```bash
cd apps/helpdesk
git status
git log --oneline -5
```

Ensure your changes are committed and pushed to the branch.

