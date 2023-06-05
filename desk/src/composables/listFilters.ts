import { startCase, isEmpty } from "lodash";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/auth";

type FrappeFilters = Record<string, Array<string>>;

const SEPARATOR_PARAM = ":";
const SEPARATOR_ITEM = " ";

export type FilterItem = {
  fieldname: string | "_assign";
  filter_type: string;
  value: string | "@me";
  label?: string;
};

export function useListFilters() {
  const route = useRoute();
  const router = useRouter();
  const authStore = useAuthStore();

  function fromQuery() {
    const { q } = route.query;

    if (isEmpty(q)) return [];
    if (Array.isArray(q)) return [];

    return decodeURI(q)
      .split(SEPARATOR_ITEM)
      .map((f) => decodeURIComponent(f))
      .map((f) => {
        const __f = f.split(SEPARATOR_PARAM);
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
        const sep = SEPARATOR_PARAM;
        const fieldname = encodeURIComponent(f.fieldname);
        const filter_type = encodeURIComponent(f.filter_type);
        const value = encodeURIComponent(f.value);

        return `${fieldname}${sep}${filter_type}${sep}${value}`;
      })
      .join(SEPARATOR_ITEM);
  }

  function toFrappeFilter(f: Array<FilterItem>): FrappeFilters {
    return f.reduce((p, c) => {
      transformOperator(c);
      transformValue(c);

      p[c.fieldname] = [c.filter_type, c.value];

      return p;
    }, {});
  }

  function queryFilters() {
    return toFrappeFilter(fromQuery());
  }

  function transformOperator(f: FilterItem) {
    f.filter_type = f.filter_type.toLowerCase();

    if (f.fieldname === "_assign") {
      if (f.filter_type === "is") f.filter_type = "like";
      if (f.filter_type === "is not") f.filter_type = "not like";
    }

    switch (f.filter_type) {
      case "is":
        f.filter_type = "=";
        break;
      case "is not":
        f.filter_type = "!=";
        break;
      case "before":
        f.filter_type = "<";
        break;
      case "after":
        f.filter_type = ">";
    }

    return f.filter_type;
  }

  function transformValue(f: FilterItem) {
    if (f.value === "@me") f.value = authStore.userId;

    f.value = ["like", "not like"].includes(f.filter_type)
      ? `%${f.value}%`
      : f.value;

    return f.value;
  }

  function transformLabel(f: FilterItem) {
    f.label = startCase(f.fieldname);
    if (f.fieldname === "_assign") f.label = "Assigned To";
    return f;
  }

  function queryOrderBy() {
    const { sort, sortDirection } = route.query;

    if (!sort) return;
    if (sort instanceof Array) return;

    const sortBy = decodeURIComponent(sort).replaceAll("-", " ");
    return [sortBy, sortDirection].join(" ").trim();
  }

  function applyQuery(query: Array<FilterItem> | string) {
    const q = typeof query === "string" ? query : toQuery(query);
    router.push({ query: { ...route.query, q } });
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
