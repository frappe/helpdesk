import frappe
from bs4 import BeautifulSoup
from frappe.query_builder.functions import Count
from openai import OpenAI


def get_tickets_with_big_threads():

    Tickets = frappe.qb.DocType("HD Ticket")
    Emails = frappe.qb.DocType("Communication")
    Comments = frappe.qb.DocType("HD Ticket Comment")

    ticket_emails_threshold = 15

    tickets = (
        frappe.qb.from_(Emails)
        .select(Emails.reference_name)
        .left_join(Comments)
        .on(Emails.reference_name == Comments.reference_ticket)
        .where(Emails.reference_doctype == "HD Ticket")
        .groupby(Emails.reference_name)
        .where(Emails.creation > "2025-01-01")
        .having(Count(Emails.name) + Count(Comments.name) > ticket_emails_threshold)
    ).run(pluck="reference_name")

    content = []
    for t in tickets:
        data = {}
        emails = frappe.get_all(
            "Communication",
            pluck="content",
            filters={"reference_doctype": "HD Ticket", "reference_name": t},
        )
        comments = frappe.get_all(
            "HD Ticket Comment", pluck="content", filters={"reference_ticket": t}
        )
        # breakpoint()
        emails, comments = parse_email_comments(emails, comments)

        emails = ", ".join(emails)
        comments = ", ".join(comments)

        data[t] = {
            "name": t,
            "emails": f"{emails}",
            "comments": f"{comments}",
        }
        content.append(data)


def parse_email_comments(emails, comments):
    parsed_emails = []
    parsed_comments = []
    for email in emails:
        author = email.sender
        content = email.content
        stripped_content = strip_tags(content)
        parsed_emails.append(f"{author}: {stripped_content}")

    for comment in comments:
        author = comment.commented_by
        content = comment.content
        stripped_content = strip_tags(content)
        parsed_comments.append(f"{author}: {stripped_content}")

    return parsed_emails, parsed_comments


def strip_tags(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.insert_after("\n")
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        heading.insert_after("\n")
    return soup.get_text()


def get_openai_client():
    OPENAI_KEY = frappe.conf.get("openai_key")
    return OpenAI(api_key=OPENAI_KEY)
