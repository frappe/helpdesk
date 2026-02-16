import frappe

def notify_project_manager_on_ticket_create(doc, method=None):

    if not doc.custom_project:
        return

    # Project Manager (Employee)
    project_manager = frappe.db.get_value(
        "Project",
        doc.custom_project,
        "custom_project_manager"
    )

    if not project_manager:
        return

    # Employee → User
    user_id = frappe.db.get_value(
        "Employee",
        project_manager,
        "user_id"
    )

    if not user_id:
        return

    # User → Email
    user_email = frappe.db.get_value(
        "User",
        user_id,
        "email"
    )

    if not user_email:
        return

    # 🔹 Raised User Name
    raised_user_name = frappe.db.get_value(
        "User",
        doc.raised_by,
        "full_name"
    ) or doc.raised_by

    # 🔹 System User Name
    system_user_name = frappe.db.get_value(
        "User",
        doc.owner,
        "full_name"
    ) or doc.owner

    # 🔹 Project Name
    project_name = frappe.db.get_value(
        "Project",
        doc.custom_project,
        "project_name"
    ) or doc.custom_project

    # Ticket URL
    ticket_url = frappe.utils.get_url(
        f"/helpdesk/tickets/{doc.name}"
    )

    subject = f"New Helpdesk Ticket Raised - {doc.name}"

    message = f"""
    <div style="font-family: Arial; font-size:14px;">

    <p>Hello,</p>

    <p>A new <b>Helpdesk Ticket</b> has been raised.</p>

    <table border="1" cellpadding="8" cellspacing="0"
           style="border-collapse: collapse;">

        <tr>
            <td><b>Ticket ID</b></td>
            <td>{doc.name}</td>
        </tr>

        <tr>
            <td><b>Subject</b></td>
            <td>{doc.subject}</td>
        </tr>

        <tr>
            <td><b>Project</b></td>
            <td>{project_name}</td>
        </tr>

        <tr>
            <td><b>Raised By</b></td>
            <td>{raised_user_name}</td>
        </tr>

    </table>

    <br>

    <a href="{ticket_url}"
       style="
            background:#4CAF50;
            color:white;
            padding:10px 15px;
            text-decoration:none;
            border-radius:5px;
       ">
       View Ticket
    </a>

    <br><br>

    Regards,<br>
    <b>Helpdesk System</b>

    </div>
    """

    frappe.sendmail(
        recipients=[user_email],
        subject=subject,
        message=message
    )
  