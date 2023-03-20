import { createListResource, createResource } from "frappe-ui";

const GET_LIST_METHOD = "frappedesk.extends.client.get_list";
const GET_LIST_META_METHOD = "frappedesk.extends.client.get_list_meta";

type ListOptions = {
	doctype: string;
	fields?: Array<string>;
	filters?: object;
	orderBy?: string;
	pageLength?: number;
	start?: number;
	cache?: boolean | string | Array<string>;
};

type MetaData = {
	total_count: number;
	total_pages: number;
	current_page: number;
	has_next_page: boolean;
	has_previous_page: boolean;
};

export function createListManager(options: ListOptions) {
	const doctype = options.doctype;
	const fields = options.fields;
	const filters = options.filters;
	const orderBy = options.orderBy;
	const pageLength = options.pageLength;
	const start = options.start;
	const cache = options.cache;

	const list = createListResource({
		type: "list",
		url: GET_LIST_METHOD,
		doctype,
		fields,
		orderBy,
		filters,
		pageLength,
		start,
		cache,
		auto: true,
		debug: true,
	});

	createResource({
		url: GET_LIST_META_METHOD,
		params: {
			doctype,
			filters,
			limit: pageLength,
			orderBy,
			start,
		},
		onSuccess: (data: MetaData) => {
			Object.assign(list, {
				totalCount: data.total_count,
				totalPages: data.total_pages,
				currentPage: data.current_page,
				hasNextPage: data.has_next_page,
				hasPreviousPage: data.has_previous_page,
			});
		},
		auto: true,
		debug: true,
	});

	return list;
}
