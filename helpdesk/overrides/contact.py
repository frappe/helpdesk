import frappe
from frappe.contacts.doctype.contact.contact import Contact
from frappe.query_builder.functions import Avg

from helpdesk.utils import get_country_from_timezone, get_customers


def before_insert(doc, method=None):
    if doc.email_id:
        domain = doc.email_id.split("@")[1]
        hd_customers = frappe.get_all(
            "HD Customer", filters={"domain": domain}, fields=["name"]
        )
        if hd_customers:
            doc.append(
                "links",
                {"link_doctype": "HD Customer", "link_name": hd_customers[0].name},
            )


class CustomContact(Contact):
    @frappe.whitelist()
    def get_info(self):
        rating = self.get_avg_rating()
        customers = get_customers_with_image(self.name)

        result = {"rating": rating, "customers": customers}
        if self.user:
            time_zone = frappe.db.get_value("User", self.user, "time_zone")
            if time_zone:
                result["time_zone"] = time_zone
                result["country"] = get_country_from_timezone(time_zone)
        return result

    def get_avg_rating(self):
        HDTicket = frappe.qb.DocType("HD Ticket")
        avg_rating = (
            frappe.qb.from_(HDTicket)
            .select(Avg(HDTicket.feedback_rating))
            .where(HDTicket.contact == self.name)
        ).run()[0][0]
        return avg_rating


def get_customers_with_image(contact_name: str):
    customers = get_customers(contact=contact_name)
    result = []
    for customer in customers:
        image = frappe.db.get_value("HD Customer", customer, "image")
        result.append({"name": customer, "image": image})
    return result
