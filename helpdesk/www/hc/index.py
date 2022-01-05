import frappe

def get_context(context):
    context.categories = frappe.get_all('Category', fields=['name', 'description', 'thumbnail'])
    context.articles = frappe.get_all('Article')
    return context