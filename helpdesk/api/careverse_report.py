import frappe
from frappe.utils import add_days, escape_html
from frappe.utils.pdf import get_pdf


def careverse_report_pdf(from_date, to_date):
    """PDF summary for care-team users: Careverse tickets only."""
    from helpdesk.api.report_export import _get_summary_metrics

    summary = _get_summary_metrics(from_date, to_date, None)
    tickets = frappe.get_list(
        "HD Ticket",
        filters=[["brand", "=", "Careverse"], ["creation", ">=", from_date],
                 ["creation", "<", add_days(to_date, 1)]],
        fields=["name", "subject", "status", "priority", "raised_by", "facility", "creation"],
        order_by="creation desc", limit_page_length=0)

    def row(cells, tag="td"):
        return "<tr>" + "".join(f"<{tag}>{escape_html(str(c or ''))}</{tag}>" for c in cells) + "</tr>"

    html = (
        "<h2>Careverse Support Report</h2>"
        f"<p>{escape_html(str(from_date))} to {escape_html(str(to_date))}</p>"
        "<h3>Summary</h3><table border='1' cellpadding='4' cellspacing='0'>"
        + row(summary[0], "th") + "".join(row(r) for r in summary[1:]) + "</table>"
        "<h3>Tickets</h3><table border='1' cellpadding='4' cellspacing='0'>"
        + row(["Ticket", "Subject", "Status", "Priority", "Raised By", "Facility", "Created"], "th")
        + "".join(row([t.name, t.subject, t.status, t.priority, t.raised_by, t.facility, t.creation]) for t in tickets)
        + "</table>"
    )
    frappe.response["filename"] = f"Careverse_Report_{from_date}_to_{to_date}.pdf"
    frappe.response["filecontent"] = get_pdf(html)
    frappe.response["type"] = "pdf"
