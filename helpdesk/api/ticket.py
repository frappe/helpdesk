# ticket api
import frappe

from helpdesk.openai import get_openai_client, parse_email_comments


def assign_ticket_to_agent(ticket_id, agent_id=None):
    if not ticket_id:
        return

    ticket_doc = frappe.get_doc("HD Ticket", ticket_id)

    if not agent_id:
        # assign to self
        agent_id = frappe.session.user

    if not frappe.db.exists("HD Agent", agent_id):
        frappe.throw("Tickets can only assigned to agents")

    ticket_doc.assign_agent(agent_id)
    return ticket_doc


@frappe.whitelist()
def bulk_assign_ticket_to_agent(ticket_ids, agent_id=None):
    if ticket_ids:
        ticket_docs = []
        for ticket_id in ticket_ids:
            ticket_doc = assign_ticket_to_agent(ticket_id, agent_id)
            ticket_docs.append(ticket_doc)
        return ticket_docs


client = get_openai_client()


@frappe.whitelist()
def summarise_ticket(ticket_id):

    emails = frappe.get_all(
        "Communication",
        pluck="content",
        filters={"reference_doctype": "HD Ticket", "reference_name": ticket_id},
    )
    comments = frappe.get_all(
        "HD Ticket Comment", pluck="content", filters={"reference_ticket": ticket_id}
    )
    emails, comments = parse_email_comments(emails, comments)

    emails = ", ".join(emails)
    comments = ", ".join(comments)

    method1(ticket_id, emails, comments)
    method2(ticket_id, emails, comments)


def method1(ticket_id, emails, comments):
    content = """
    You are a text summarizer. Your job is to summarize the support ticket in a concise, actionable format. Extract:
        1. Key issue or request: This can be a bit longer to provide context. Explain why the issue is caused or what the request is. How it has been tried to solve.
        2. Relevant context (product, version, environment)
        3. Customer's goal or desired outcome
        4. Any blockers or urgency indicators
        Limit summary to max of 600 characters. Focus on facts, not sentiment. Give a clear, concise summary such that any agent reading it can understand the ticket and take action.
     Format should be markdown with bullet points,headings mentioned should be bold. Should be easy to read and understand for the agents.
    """
    msg = f"The ticket {ticket_id} has the following emails: {emails} and comments: {comments}. Please summarise the ticket."
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": content},
            {"role": "user", "content": msg},
        ],
    )
    print("FIRST METHOD")
    print("\n\n", completion.choices[0].message.content, "\n\n")


def method2(ticket_id, emails, comments):
    # FIRST PASS: Create detailed notes from all content
    first_pass_prompt = """
    You are a support ticket analyzer. Create detailed notes on this ticket by:
    1. Organizing the conversation chronologically
    2. Identifying key technical details, error messages, and attempted solutions
    3. Noting any changes in scope or requirements
    4. Highlighting customer expectations and frustrations
    5. Tracking action items and ownership

    Format as detailed notes that capture the complete picture of the ticket's evolution and current state.
    Use markdown formatting with headings and bullet points for clarity.
    """

    first_pass_msg = f"The ticket {ticket_id} has the following emails: {emails} and internal team comments: {comments}. Please analyze this content."

    first_pass_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": first_pass_prompt},
            {"role": "user", "content": first_pass_msg},
        ],
    )

    detailed_notes = first_pass_completion.choices[0].message.content

    print("SECOND METHOD")

    second_pass_msg = f"Based on these detailed notes from ticket {ticket_id}, create a final concise summary: {detailed_notes}"

    second_pass_prompt = """
    You are a text summarizer. Your job is to summarize the support ticket in a concise, actionable format. Extract:
    1. Key issue or request: This can be a bit longer to provide context. Explain why the issue is caused or what the request is. How it has been tried to solve.
    2. Relevant context (product, version, environment)
    3. Customer's goal or desired outcome
    4. Any blockers or urgency indicators
    
    Limit summary to max of 600 characters. Focus on facts, not sentiment. Give a clear, concise summary such that any agent reading it can understand the ticket and take action.
    Format should be markdown with bullet points, headings mentioned should be bold. Should be easy to read and understand for the agents.
    """

    final_summary_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": second_pass_prompt},
            {"role": "user", "content": second_pass_msg},
        ],
    )
    print("\n\n", "Final Summary M2")
    print(final_summary_completion.choices[0].message.content, "\n\n")
