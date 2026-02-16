import frappe


def notify_customer_on_manager_reply(doc, method=None):

    if doc.reference_doctype != "HD Ticket":
        return

    if not doc.reference_name:
        return

    ticket = frappe.get_doc("HD Ticket", doc.reference_name)

    # ------------------------------------------------
    # Customer Email
    # ------------------------------------------------
    customer_email = frappe.db.get_value(
        "User",
        ticket.raised_by,
        "email"
    )

    if not customer_email:
        return

    # ------------------------------------------------
    # Detect if Manager Reply
    # ------------------------------------------------
    sender_email = doc.sender or ""

    if "<" in sender_email:
        sender_email = sender_email.split("<")[-1].replace(">", "").strip()

    # Skip if Customer reply
    if sender_email == customer_email:
        return

    # =====================================================
    # CC 1️⃣ Default Email
    # =====================================================
    default_email = frappe.db.get_value(
        "Email Account",
        {"default_outgoing": 1},
        "email_id"
    )

    # =====================================================
    # CC 2️⃣ Project Manager
    # =====================================================
    project_manager_email = None

    if ticket.get("custom_project"):

        pm_emp = frappe.db.get_value(
            "Project",
            ticket.custom_project,
            "custom_project_manager"
        )

        if pm_emp:
            user_id = frappe.db.get_value(
                "Employee",
                pm_emp,
                "user_id"
            )

            if user_id:
                project_manager_email = frappe.db.get_value(
                    "User",
                    user_id,
                    "email"
                )

    # =====================================================
    # CC 3️⃣ Current User (Reply Sender)
    # =====================================================
    current_user_email = sender_email

    # =====================================================
    # FINAL CC LIST
    # =====================================================
    cc_list = list(set(filter(None, [
        default_email,
        project_manager_email,
        current_user_email
    ])))

    # Remove customer duplicate
    if customer_email in cc_list:
        cc_list.remove(customer_email)

    # ------------------------------------------------
    # DEBUG PRINT (see in logs)
    # ------------------------------------------------
    frappe.logger().info(f"""
    Manager Reply Mail Debug
    TO: {customer_email}
    CC: {cc_list}
    """)

    # ------------------------------------------------
    # Mail Content
    # ------------------------------------------------
    ticket_url = frappe.utils.get_url(
    f"/helpdesk/tickets/{ticket.name}"
    )

    project_name = frappe.db.get_value(
        "Project",
        ticket.custom_project,
        "project_name"
    ) if ticket.custom_project else "-"

    raised_by_name = frappe.db.get_value(
        "User",
        ticket.raised_by,
        "full_name"
    )

    replied_by_name = doc.sender_full_name or doc.sender

    status = ticket.status or "-"
    priority = ticket.priority or "-"


    frappe.sendmail(
        recipients=[customer_email],
        cc=cc_list,
        subject=f"Update on Your Ticket #{ticket.name}",
        message=f"""
    <div style="font-family: Arial, sans-serif; font-size:14px; color:#333;">

        <p>Hello <b>{raised_by_name}</b>,</p>

        <p>
            There is a new update on your Helpdesk Ticket.
            Our support team has responded to your query.
        </p>

        <table style="
            border-collapse: collapse;
            width: 100%;
            max-width: 600px;
            border:1px solid #ddd;
        " cellpadding="8">

            <tr style="background:#f5f5f5;">
                <td><b>Ticket ID</b></td>
                <td>{ticket.name}</td>
            </tr>

            <tr>
                <td><b>Subject</b></td>
                <td>{ticket.subject}</td>
            </tr>

            <tr style="background:#f5f5f5;">
                <td><b>Project</b></td>
                <td>{project_name}</td>
            </tr>

            <tr>
                <td><b>Status</b></td>
                <td>{status}</td>
            </tr>

            <tr style="background:#f5f5f5;">
                <td><b>Priority</b></td>
                <td>{priority}</td>
            </tr>

            <tr>
                <td><b>Raised By</b></td>
                <td>{raised_by_name}</td>
            </tr>

            <tr style="background:#f5f5f5;">
                <td><b>Replied By</b></td>
                <td>{replied_by_name}</td>
            </tr>

        </table>

        <br>

        <a href="{ticket_url}"
        style="
                display:inline-block;
                background:#4CAF50;
                color:white;
                padding:12px 18px;
                text-decoration:none;
                border-radius:6px;
                font-weight:bold;
        ">
        🔍 View Ticket
        </a>

        <br><br>

        Regards,<br>
        <b>Helpdesk Support Team</b><br>
        Ethical Intelligent Technologies

    </div>
    """
    )



# ============================================================
# 2️⃣ Customer Reply → Manager / Team
# ============================================================
def notify_team_on_customer_reply(doc, method=None):

    if doc.reference_doctype != "HD Ticket":
        return

    if not doc.reference_name:
        return

    ticket = frappe.get_doc("HD Ticket", doc.reference_name)

    # ------------------------------------------------
    # Customer Email
    # ------------------------------------------------
    customer_email = frappe.db.get_value(
        "User",
        ticket.raised_by,
        "email"
    )

    # Run only if Customer replied
    if doc.sender != customer_email:
        return

    # =====================================================
    # TO → Default Email
    # =====================================================
    default_email = frappe.db.get_value(
        "Email Account",
        {"default_outgoing": 1},
        "email_id"
    )

    if not default_email:
        return

    # =====================================================
    # CC → Project Manager
    # =====================================================
    project_manager_email = None

    if ticket.get("custom_project"):

        pm_emp = frappe.db.get_value(
            "Project",
            ticket.custom_project,
            "custom_project_manager"
        )

        if pm_emp:
            user_id = frappe.db.get_value(
                "Employee",
                pm_emp,
                "user_id"
            )

            if user_id:
                project_manager_email = frappe.db.get_value(
                    "User",
                    user_id,
                    "email"
                )

    cc_list = list(set(filter(None, [
        project_manager_email
    ])))

    # ------------------------------------------------
    # Mail Content
    # ------------------------------------------------
    ticket_url = frappe.utils.get_url(
        f"/helpdesk/tickets/{ticket.name}"
    )

    # -----------------------------
    # Extra Details
    # -----------------------------
    project_name = frappe.db.get_value(
        "Project",
        ticket.custom_project,
        "project_name"
    ) if ticket.custom_project else "-"

    customer_name = frappe.db.get_value(
        "User",
        ticket.raised_by,
        "full_name"
    ) or ticket.raised_by

    status = ticket.status or "-"
    priority = ticket.priority or "-"
    subject = f"Customer Reply Received | Ticket #{ticket.name}"

    # -----------------------------
    # Professional Mail Content
    # -----------------------------
    message = f"""
    <div style="font-family: Arial, sans-serif; font-size:14px; color:#333;">

        <p>Hello Team,</p>

        <p>
            A <b>customer has responded</b> to the following Helpdesk Ticket.
            Please review the update and proceed with the necessary action.
        </p>

        <br>

        <!-- Ticket Overview Table -->
        <table style="
            border-collapse: collapse;
            width: 100%;
            max-width: 650px;
            border:1px solid #e0e0e0;
        " cellpadding="10">

            <tr style="background-color:#f7f7f7;">
                <td><b>Ticket ID</b></td>
                <td>{ticket.name}</td>
            </tr>

            <tr>
                <td><b>Subject</b></td>
                <td>{ticket.subject}</td>
            </tr>

            <tr style="background-color:#f7f7f7;">
                <td><b>Project</b></td>
                <td>{project_name}</td>
            </tr>

            <tr>
                <td><b>Customer</b></td>
                <td>{customer_name}</td>
            </tr>

            <tr style="background-color:#f7f7f7;">
                <td><b>Status</b></td>
                <td>{status}</td>
            </tr>

            <tr>
                <td><b>Priority</b></td>
                <td>{priority}</td>
            </tr>

        </table>

        <br>

        <!-- Button -->
        <a href="{ticket_url}"
        style="
                display:inline-block;
                background-color:#1976D2;
                color:#ffffff;
                padding:12px 20px;
                text-decoration:none;
                border-radius:6px;
                font-weight:bold;
        ">
        📂 Open Ticket
        </a>

        <br>

        <br>

        Regards,<br>
        <b>Helpdesk Support Team</b><br>
        Ethical Intelligent Technologies

    </div>
    """

    # -----------------------------
    # Send Mail
    # -----------------------------
    frappe.sendmail(
        recipients=[default_email],  # TO
        cc=cc_list,                  # CC
        subject=subject,
        message=message
    )
