import { ref, onMounted } from "vue";
import { createListResource, createResource } from "frappe-ui";
import { useListFilters } from "./listFilters";
import { isEmpty } from "lodash";

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
	const filters = ref(options.filters);
	const orderBy = ref(options.orderBy);
	const pageLength = options.pageLength;
	const start = options.start;
	const cache = options.cache;
	const filterManager = useListFilters();

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
		onSuccess() {
			meta.fetch();
		},
		auto: true,
		debug: true,
	});

	const meta = createResource({
		url: GET_LIST_META_METHOD,
		params: {
			doctype,
			filters: filters.value,
			limit: pageLength,
			orderBy: orderBy.value,
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
		debug: true,
	});

	onMounted(() => {
		const queryFilters = filterManager.queryFilters();
		const sortBy = filterManager.queryOrderBy();

		if (!isEmpty(queryFilters)) filters.value = queryFilters;
		if (sortBy) orderBy.value = sortBy;

		list.reload();
	})

	return list;
}
