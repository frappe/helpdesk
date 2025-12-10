"""
Run this on PRODUCTION server to diagnose the reply_via_agent issue

Usage on production:
    bench --site <site-name> console
    Then paste this entire script
"""
import inspect
import frappe

# Initialize Frappe
frappe.init()
frappe.connect()

print("=" * 80)
print("PRODUCTION DIAGNOSTIC: reply_via_agent Method Check")
print("=" * 80)
print()

# Method 1: Check via import
try:
    from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket
    print("✅ Successfully imported HDTicket class")
    
    # Get method signature
    if hasattr(HDTicket, 'reply_via_agent'):
        sig = inspect.signature(HDTicket.reply_via_agent)
        print(f"✅ Method exists: reply_via_agent")
        print(f"   Signature: {sig}")
        print()
        
        # Check parameters
        params = list(sig.parameters.keys())
        print(f"   Parameters: {params}")
        print()
        
        if 'email_account' in params:
            print("✅ SUCCESS: email_account parameter EXISTS")
            email_param = sig.parameters['email_account']
            print(f"   Parameter details: {email_param}")
        else:
            print("❌ ERROR: email_account parameter MISSING!")
            print("   This means production code is OUTDATED")
    else:
        print("❌ ERROR: reply_via_agent method not found!")
        
except Exception as e:
    print(f"❌ ERROR importing HDTicket: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)

# Method 2: Check file directly
print("Checking source file...")
try:
    import os
    file_path = frappe.get_app_path("helpdesk", "helpdesk", "doctype", "hd_ticket", "hd_ticket.py")
    print(f"File path: {file_path}")
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            if 'email_account: str = None' in content or 'email_account=' in content:
                print("✅ Source file contains email_account parameter")
            else:
                print("❌ Source file does NOT contain email_account parameter")
                print("   This confirms production code is outdated")
                
                # Show the actual method signature in file
                import re
                match = re.search(r'def reply_via_agent\([^)]+\)', content)
                if match:
                    print(f"   Found method signature: {match.group()}")
    else:
        print(f"❌ File not found: {file_path}")
        
except Exception as e:
    print(f"❌ Error checking file: {e}")

print()
print("=" * 80)
print("RECOMMENDATION:")
print("If email_account is missing, you need to:")
print("1. Check which branch/commit is on production")
print("2. Pull the latest code with email_account parameter")
print("3. Clear Python cache: find . -name '*.pyc' -delete && find . -type d -name __pycache__ -exec rm -r {} +")
print("4. Restart: bench restart")
print("=" * 80)

frappe.destroy()

