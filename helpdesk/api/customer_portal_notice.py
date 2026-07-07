import frappe

NOTICE_FLAG = "show_customer_portal_permission_notice"


@frappe.whitelist(methods=["POST"])
def dismiss_notice() -> None:
    """Permanently dismiss the customer portal permission change notice."""
    only_for_managers()
    disable_notice()


@frappe.whitelist(methods=["POST"])
def restore_ticket_access() -> None:
    """Restore pre-migration ticket visibility for customer contacts.

    Promotes every customer contact to a customer manager in a background
    job, so each contact can again see all tickets of their customer.
    Dismisses the notice once the job is queued.
    """
    only_for_managers()
    frappe.enqueue(
        promote_all_contacts_to_managers,
        queue="long",
        job_id="promote_all_contacts_to_managers",
        deduplicate=True,
    )
    disable_notice()


def disable_notice() -> None:
    """Turn the flag off via the document, so HD Settings notifies
    connected clients through its on_update realtime event."""
    settings = frappe.get_doc("HD Settings")
    settings.set(NOTICE_FLAG, 0)
    settings.save(ignore_permissions=True)


def promote_all_contacts_to_managers() -> None:
    """Mark every customer contact as manager, syncing roles via HD Customer."""
    customers = frappe.get_all(
        "HD Customer Member",
        filters={"is_manager": 0, "parenttype": "HD Customer"},
        parent_doctype="HD Customer",
        pluck="parent",
        distinct=True,
    )
    for customer_name in customers:
        try:
            promote_customer_contacts(customer_name)
        except Exception:
            frappe.log_error(
                title="promote_all_contacts_to_managers",
                message=f"Failed to promote contacts of customer {customer_name}",
            )


def promote_customer_contacts(customer_name: str) -> None:
    customer = frappe.get_doc("HD Customer", customer_name)
    for contact in customer.contacts:
        contact.is_manager = True
    customer.save(ignore_permissions=True)


def only_for_managers() -> None:
    frappe.only_for(["Agent Manager", "System Manager"])
