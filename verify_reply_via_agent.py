"""
Script to verify reply_via_agent method signature on production
Run this on production server to check if the method has email_account parameter
"""
import frappe
import inspect

def verify_method_signature():
    frappe.init()
    frappe.connect()
    
    from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket
    
    # Get method signature
    sig = inspect.signature(HDTicket.reply_via_agent)
    
    print("=" * 60)
    print("HDTicket.reply_via_agent Method Signature:")
    print("=" * 60)
    print(sig)
    print()
    
    # Check if email_account parameter exists
    params = list(sig.parameters.keys())
    has_email_account = 'email_account' in params
    
    print("Parameters:", params)
    print()
    
    if has_email_account:
        print("✅ SUCCESS: email_account parameter EXISTS in method signature")
        email_account_param = sig.parameters['email_account']
        print(f"   Parameter details: {email_account_param}")
    else:
        print("❌ ERROR: email_account parameter MISSING from method signature")
        print("   This means production doesn't have the latest code!")
    
    print("=" * 60)
    
    frappe.destroy()

if __name__ == "__main__":
    verify_method_signature()

