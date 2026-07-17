import type { ListResource, Resource } from "@/types";
import type { HDTicket } from "@/types/doctypes";
import { createListResource, createResource } from "frappe-ui";

export function getTicketListResource(): {
	ticketsListResource: ListResource<HDTicket>;
	ticketsCountResource: Resource<number>;
} {
	const ticketsListResource = createListResource({
		doctype: "HD Ticket",
		pageLength: 20,
		fields: [
			"name",
			"subject",
			"status",
			"priority",
			"creation",
			"modified",
			"_assign",
			"response_by",
			"resolution_by",
		],
		orderBy: "modified desc",
	});

	// Permission-aware total for the current filters (unlike data.length,
	// which only counts the fetched pages).
	const ticketsCountResource = createResource({
		url: "frappe.desk.reportview.get_count",
		makeParams: () => ({
			doctype: "HD Ticket",
			filters: ticketsListResource.filters,
			or_filters: ticketsListResource.orFilters,
		}),
	});

	return { ticketsListResource, ticketsCountResource };
}
