import { useRouter, useRoute } from "vue-router";
import { startCase, isEmpty } from "lodash";

type FrappeFilters = Record<string, Array<string>>;

export type FilterItem = {
	fieldname: string | "_assign";
	filter_type: string;
	value: string | "@me";
	label?: string;
};

export function useListFilters() {
	const route = useRoute();
	const router = useRouter();

	function fromQuery() {
		const { q } = route.query;

		if (isEmpty(q)) return [];
		if (Array.isArray(q)) return [];

		return decodeURI(q)
			.split("+")
			.map((f) => decodeURIComponent(f))
			.map((f) => {
				const __f = f.split(":");
				const fieldname = __f.shift();
				const filter_type = __f.shift();
				const value = __f.shift();

				return {
					fieldname,
					filter_type,
					value,
				};
			})
			.map(transformLabel);
	}

	function toQuery(filters: Array<FilterItem>) {
		return filters
			.map((f) => {
				return `${f.fieldname}:${f.filter_type}:${f.value}`;
			})
			.map((f) => encodeURIComponent(f))
			.join("+");
	}

	function toFrappeFilter(f: Array<FilterItem>): FrappeFilters {
		return f.reduce((p, c) => {
			const operator = transformOperator(c);
			const value = transformValue(c);

			p[c.fieldname] = [operator, value];
			return p;
		}, {});
	}

	function queryFilters() {
		const filters = fromQuery();
		const frappeFilters = toFrappeFilter(filters);

		return frappeFilters;
	}

	function transformOperator(f: FilterItem): string {
		if (f.fieldname === "_assign") {
			if (f.filter_type === "is") f.filter_type = "like";
			if (f.filter_type === "is not") f.filter_type = "not like";
		}

		switch (f.filter_type) {
			case "is":
				return "=";
			case "is not":
				return "!=";
			case "before":
				return "<";
			case "after":
				return ">";
			default:
				return f.filter_type;
		}
	}

	function transformValue(f: FilterItem) {
		f.value = f.value === "@me" ? getMe() : f.value;
		const v = f.value;

		switch (f.filter_type) {
			case "like":
				return `%${v}%`;
			case "not like":
				return `%${v}%`;
			default:
				return v;
		}
	}

	// TODO:
	function getMe() {
		return "hello@ssiyad.com";
	}

	function transformLabel(f: FilterItem) {
		f.label = startCase(f.fieldname);
		if (f.fieldname === "_assign") f.label = "Assigned To";
		return f;
	}

	function queryOrderBy() {
		const { sortBy, sortDirection = "desc" } = route.query;

		if (!sortBy) return;

		return `${sortBy} ${sortDirection}`;
	}

	function applyQuery(query: string) {
		router.push({ query: { ...route.query, q: query } });
	}

	return {
		applyQuery,
		fromQuery,
		queryFilters,
		queryOrderBy,
		toFrappeFilter,
		toQuery,
	};
}
