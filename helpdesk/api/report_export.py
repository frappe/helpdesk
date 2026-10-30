"""
Management report export — combines existing HD Ticket reports and dashboard
SLA metrics into a single downloadable Excel workbook (multi-sheet) or PDF
executive summary, for on-demand monthly reporting to management.
"""

from io import BytesIO

import frappe
import xlsxwriter
from frappe import _
from frappe.desk.query_report import build_xlsx_data
from frappe.utils.pdf import get_pdf
from frappe.utils.xlsxutils import make_xlsx

from helpdesk.api.dashboard import HelpdeskDashboard, _locked_brand
from helpdesk.utils import agent_only


def _get_summary_metrics(from_date, to_date, county=None):
    """Reuse the same SLA/number-card logic as the dashboards."""
    filters = frappe._dict(
        from_date=from_date,
        to_date=to_date,
        team=None,
        agent=None,
        county=county,
        support_level=None,
    )
    dashboard = HelpdeskDashboard(filters)
    cards = dashboard.get_number_card_data()

    rows = [["Metric", "Value", "Delta / Target"]]
    for card in cards:
        value = card.get("value")
        suffix = card.get("suffix", "")
        delta_suffix = card.get("deltaSuffix", "")
        delta = card.get("delta")
        value_str = f"{round(value, 2) if isinstance(value, float) else value}{suffix}"
        delta_str = f"{round(delta, 2) if isinstance(delta, float) else delta}{delta_suffix}" if delta is not None else ""
        rows.append([card.get("title"), value_str, delta_str])
    return rows


def _run_existing_report(module_path, filters):
    """Call an existing Script Report's execute() and return (columns, data)."""
    module = frappe.get_module(module_path)
    result = module.execute(filters)
    columns, data = result[0], result[1]
    return columns, data


def _add_report_sheet(wb, sheet_name, columns, data, report_name=""):
    report_data = frappe._dict(
        {
            "report_name": report_name or sheet_name,
            "filters": {},
            "columns": columns,
            "result": data,
        }
    )
    # build_styles=False — avoids build_xlsx_data trying to look up a real
    # "Report" doctype record matching our sheet name for style config, which
    # doesn't exist since these are ad-hoc combined sheets, not registered reports.
    xlsx_data, column_widths, styles = build_xlsx_data(
        report_data, [], 1, ignore_visible_idx=True, build_styles=False
    )
    make_xlsx(xlsx_data, sheet_name, wb=wb, column_widths=column_widths, styles=styles)


def _careverse_report_excel(from_date, to_date):
    """Scoped workbook for care-team users: Careverse tickets only."""
    xlsx_file = BytesIO()
    wb = xlsxwriter.Workbook(xlsx_file, {"constant_memory": True})
    make_xlsx(_get_summary_metrics(from_date, to_date, None), "Summary", wb=wb)

    fields = ["name", "subject", "status", "priority", "ticket_type", "agent_group",
              "raised_by", "facility", "county", "creation", "resolution_date", "agreement_status"]
    tickets = frappe.get_list(
        "HD Ticket",
        filters=[["brand", "=", "Careverse"], ["creation", ">=", from_date],
                 ["creation", "<", frappe.utils.add_days(to_date, 1)]],
        fields=fields, order_by="creation desc", limit_page_length=0)
    rows = [["Ticket", "Subject", "Status", "Priority", "Type", "Team", "Raised By",
             "Facility", "County", "Created", "Resolved", "SLA"]]
    for t in tickets:
        rows.append([str(t.get(f) or "") for f in fields])
    make_xlsx(rows, "Tickets", wb=wb)
    wb.close()

    frappe.response["filename"] = f"Careverse_Report_{from_date}_to_{to_date}.xlsx"
    frappe.response["filecontent"] = xlsx_file.getvalue()
    frappe.response["content_type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    frappe.response["type"] = "download"


@frappe.whitelist()
@agent_only
def get_management_report_excel(from_date: str, to_date: str, county: str = None):
    if _locked_brand():
        return _careverse_report_excel(from_date, to_date)
    """Build and download a multi-sheet Excel management report."""
    xlsx_file = BytesIO()
    wb = xlsxwriter.Workbook(xlsx_file, {"constant_memory": True})

    # 1. Summary sheet — SLA/number cards vs target
    summary_rows = _get_summary_metrics(from_date, to_date, county)
    make_xlsx(summary_rows, "Summary", wb=wb)

    # 2. County breakdown
    county_filters = {"from_date": from_date, "to_date": to_date}
    if county:
        county_filters["county"] = county
    columns, data = _run_existing_report(
        "helpdesk.helpdesk.report.county_ticket_analysis.county_ticket_analysis",
        county_filters,
    )
    _add_report_sheet(wb, "County Breakdown", columns, data)

    # 3. Ticket summary by type
    summary_filters = {"from_date": from_date, "to_date": to_date, "based_on": "Ticket Type"}
    columns, data = _run_existing_report(
        "helpdesk.helpdesk.report.ticket_summary.ticket_summary",
        summary_filters,
    )
    _add_report_sheet(wb, "Ticket Summary", columns, data)

    # 4. Monthly trend by type
    analytics_filters = {
        "from_date": from_date,
        "to_date": to_date,
        "based_on": "Ticket Type",
        "range": "Monthly",
    }
    columns, data = _run_existing_report(
        "helpdesk.helpdesk.report.ticket_analytics.ticket_analytics",
        analytics_filters,
    )
    _add_report_sheet(wb, "Monthly Trend", columns, data)

    wb.close()

    frappe.response["filename"] = f"Support_Report_{from_date}_to_{to_date}.xlsx"
    frappe.response["filecontent"] = xlsx_file.getvalue()
    frappe.response["content_type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    frappe.response["type"] = "download"


@frappe.whitelist()
@agent_only
def get_management_report_pdf(from_date: str, to_date: str, county: str = None):
    if _locked_brand():
        from helpdesk.api.careverse_report import careverse_report_pdf
        return careverse_report_pdf(from_date, to_date)
    """Build and download a one-page PDF executive summary."""
    summary_rows = _get_summary_metrics(from_date, to_date, county)

    county_filters = {"from_date": from_date, "to_date": to_date}
    if county:
        county_filters["county"] = county
    _county_columns, county_data = _run_existing_report(
        "helpdesk.helpdesk.report.county_ticket_analysis.county_ticket_analysis",
        county_filters,
    )
    top_counties = county_data[:10]

    summary_table_rows = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>"
        for r in summary_rows[1:]
    )
    county_table_rows = "".join(
        f"<tr><td>{c.county}</td><td>{c.total_tickets}</td><td>{c.resolution_rate}</td><td>{c.avg_response_time or ''}</td></tr>"
        for c in top_counties
    )

    html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Arial, sans-serif; font-size: 12px; }}
        h1 {{ font-size: 20px; }}
        h2 {{ font-size: 15px; margin-top: 24px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
        th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; }}
        th {{ background: #f0f0f0; }}
    </style>
    </head>
    <body>
        <h1>{_("Support Performance Report")}</h1>
        <p>{_("Period")}: {from_date} &mdash; {to_date}{f" | {_('County')}: {county}" if county else ""}</p>

        <h2>{_("Summary")}</h2>
        <table>
            <tr><th>{_("Metric")}</th><th>{_("Value")}</th><th>{_("Delta / Target")}</th></tr>
            {summary_table_rows}
        </table>

        <h2>{_("Top Counties by Ticket Volume")}</h2>
        <table>
            <tr><th>{_("County")}</th><th>{_("Total Tickets")}</th><th>{_("Resolved Tickets")}</th><th>{_("Avg Response (hrs)")}</th></tr>
            {county_table_rows}
        </table>
    </body>
    </html>
    """

    pdf_content = get_pdf(html)

    frappe.response["filename"] = f"Support_Report_{from_date}_to_{to_date}.pdf"
    frappe.response["filecontent"] = pdf_content
    frappe.response["content_type"] = "application/pdf"
    frappe.response["type"] = "download"
