# Production Python Cache Fix

## The Problem

Even though:
- ✅ Frontend code is correct (EmailEditor.vue matches)
- ✅ GitHub code has `email_account: str = None`
- ✅ File on disk might have the correct code

Python is still using the OLD method signature because of:
1. **Python bytecode cache** (.pyc files)
2. **Module already loaded in memory** (even after restart, if not done properly)

## Solution: Force Python to Reload

### Step 1: Verify File on Disk Has the Parameter

```bash
cd apps/helpdesk
grep "email_account: str = None" helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
```

**If this returns nothing**, the file is outdated - pull latest code first.

**If this returns the line**, the file is correct, but Python is using cached code.

### Step 2: Clear ALL Python Caches

```bash
cd apps/helpdesk

# Delete all Python bytecode files
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -name "*.pyo" -delete

# Also clear site-specific caches
cd ../..
find sites -name "*.pyc" -delete 2>/dev/null || true
find sites -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
```

### Step 3: Stop ALL Bench Processes

```bash
# Stop bench completely
bench restart --force-stop

# Or if using systemd
sudo systemctl stop bench-<site>

# Or manually kill all Python processes related to bench
ps aux | grep "bench\|frappe" | grep -v grep
# Kill those processes
```

### Step 4: Clear Frappe Cache

```bash
bench --site <site> clear-cache
bench --site <site> clear-website-cache
```

### Step 5: Restart

```bash
bench restart
```

### Step 6: Verify in Console

```bash
bench --site <site> console
```

Then run:
```python
import inspect
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket
sig = inspect.signature(HDTicket.reply_via_agent)
print(sig)
# Should show: (self, message: str, to: str = None, cc: str = None, bcc: str = None, attachments: List[str] = [], email_account: str = None)
```

## Alternative: Use the Force Reload Script

Run the `force_reload_backend.py` script in console to force Python to reload the module.

## Why This Happens

Python caches:
1. **Bytecode** (.pyc files) - compiled Python code
2. **Imported modules** (in `sys.modules`) - loaded classes/functions

Even if you:
- Update the file
- Reinstall the app
- Restart bench

Python might still use cached versions if:
- The process didn't fully restart
- Bytecode files weren't deleted
- The module is already imported in memory

## Quick Test

After fixing, try sending an email. If it still fails:
1. Check the actual error message
2. Run the verification script in console
3. Check if file on disk has the parameter

