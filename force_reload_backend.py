"""
Run this on PRODUCTION to force reload the backend module
This will clear Python's import cache and reload the HDTicket class

Usage:
    bench --site <site> console
    Then paste this entire script
"""
import sys
import frappe

# Initialize Frappe
frappe.init()
frappe.connect()

print("=" * 80)
print("FORCING BACKEND MODULE RELOAD")
print("=" * 80)
print()

# Remove the module from Python's cache
module_name = 'helpdesk.helpdesk.doctype.hd_ticket.hd_ticket'
if module_name in sys.modules:
    print(f"Removing {module_name} from sys.modules...")
    del sys.modules[module_name]
    print("✅ Removed from cache")
else:
    print(f"⚠️  {module_name} not in sys.modules")

# Also remove parent modules
parent_modules = [
    'helpdesk.helpdesk.doctype.hd_ticket',
    'helpdesk.helpdesk.doctype',
    'helpdesk.helpdesk',
    'helpdesk',
]

for mod in parent_modules:
    if mod in sys.modules:
        print(f"Removing {mod} from sys.modules...")
        del sys.modules[mod]

print()
print("=" * 80)
print("RELOADING MODULE...")
print("=" * 80)

# Force reload
import importlib
importlib.invalidate_caches()

# Now import fresh
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket

# Check method signature
import inspect
sig = inspect.signature(HDTicket.reply_via_agent)
print()
print("=" * 80)
print("CURRENT METHOD SIGNATURE:")
print("=" * 80)
print(sig)
print()

params = list(sig.parameters.keys())
if 'email_account' in params:
    print("✅ SUCCESS: email_account parameter is now loaded!")
    print(f"   All parameters: {params}")
else:
    print("❌ ERROR: email_account parameter still missing!")
    print(f"   Current parameters: {params}")
    print()
    print("This means the file on disk doesn't have the parameter.")
    print("Check: grep 'email_account: str = None' helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py")

print("=" * 80)

frappe.destroy()

