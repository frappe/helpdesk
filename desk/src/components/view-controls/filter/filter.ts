import { useDebounceFn } from "@vueuse/core";
import { createResource } from "frappe-ui";
import { computed, inject, Component, ComputedRef } from "vue";
import LucideCalendar from "~icons/lucide/calendar";
import LucideClock from "~icons/lucide/clock";
import LucideHash from "~icons/lucide/hash";
import LucideLink from "~icons/lucide/link";
import LucideList from "~icons/lucide/list";
import LucideSquareCheck from "~icons/lucide/square-check";
import LucideStar from "~icons/lucide/star";
import LucideType from "~icons/lucide/type";
import LucideUser from "~icons/lucide/user";

export interface FilterField {
  fieldname: string;
  fieldtype: string;
  label: string;
  name?: string;
  options?: string;
  value?: string;
}

export type FilterCondition = [string, string, any];

export interface ActiveFilter {
  field: FilterField;
  fieldname: string;
  operator: string;
  value: any;
  index: number;
}

export interface Filter {
  fields: ComputedRef<FilterField[]>;
  activeFilters: ComputedRef<ActiveFilter[]>;
  addFilter: (field: FilterField, operator: string, value: any) => number;
  updateFilter: (
    index: number,
    field: FilterField,
    operator: string,
    value: any
  ) => void;
  removeFilter: (index: number) => void;
  clearFilters: () => void;
  getOperators: (
    fieldtype: string,
    fieldname?: string
  ) => Array<{ label: string; value: string }>;
  getDefaultOperator: (field: FilterField) => string;
  getSelectOptions: (options?: string) => string[];
  timespanOptions: Array<{ label: string; value: string }>;
}

const typeCheck = ["Check"];
const typeLink = ["Link", "Dynamic Link"];
const typeNumber = ["Float", "Int", "Currency", "Percent"];
const typeSelect = ["Select"];
const typeString = ["Data", "Long Text", "Small Text", "Text Editor", "Text"];
const typeDate = ["Date", "Datetime"];
const typeRating = ["Rating"];

export function useFilter(): Filter {
  const listViewData = inject<any>("listViewData");
  const listViewActions = inject<any>("listViewActions");
  const { list, filterableFields } = listViewData;

  const conditions = computed<FilterCondition[]>(() =>
    normalizeFilters(list?.params?.filters || list?.data?.params?.filters)
  );

  const activeFilters = computed<ActiveFilter[]>(() => {
    if (!filterableFields.data) return [];
    const filters: ActiveFilter[] = [];
    conditions.value.forEach((condition, index) => {
      const field = filterableFields.data.find(
        (f: FilterField) => f.fieldname === condition[0]
      );
      if (!field) return;
      filters.push({
        field,
        fieldname: condition[0],
        operator: toUiOperator(condition[1]),
        value: toUiValue(field, condition[2]),
        index,
      });
    });
    return filters;
  });

  function addFilter(field: FilterField, operator: string, value: any): number {
    const next = [...conditions.value, buildCondition(field, operator, value)];
    apply(next);
    return next.length - 1;
  }

  function updateFilter(
    index: number,
    field: FilterField,
    operator: string,
    value: any
  ) {
    const next = [...conditions.value];
    next[index] = buildCondition(field, operator, value);
    apply(next);
  }

  function removeFilter(index: number) {
    const next = [...conditions.value];
    next.splice(index, 1);
    apply(next);
  }

  function clearFilters() {
    apply([]);
  }

  function apply(next: FilterCondition[]) {
    listViewActions.applyFilters(next);
  }

  return {
    fields: computed<FilterField[]>(() => filterableFields.data || []),
    activeFilters,
    addFilter,
    updateFilter,
    removeFilter,
    clearFilters,
    getOperators,
    getDefaultOperator,
    getSelectOptions,
    timespanOptions,
  };
}

export function normalizeFilters(raw: any): FilterCondition[] {
  if (!raw) return [];
  if (Array.isArray(raw)) {
    return raw
      .filter((c) => Array.isArray(c) && c.length >= 3)
      .map((c) =>
        c.length === 4
          ? ([c[1], c[2], c[3]] as FilterCondition)
          : ([c[0], c[1], c[2]] as FilterCondition)
      );
  }
  return Object.entries(raw).flatMap(([fieldname, value]): FilterCondition[] => {
    if (Array.isArray(value)) {
      if (Array.isArray(value[0])) {
        return value.map((condition) => [
          fieldname,
          condition[0],
          condition[1],
        ]);
      }
      return [[fieldname, value[0], value[1]]];
    }
    return [[fieldname, "=", value]];
  });
}

export function useLinkSearch(doctype: string) {
  const results = createResource({
    url: "frappe.desk.search.search_link",
    method: "POST",
    params: { txt: "", doctype, page_length: 10 },
    transform: (data: any[]) => {
      const options = data.map((option) => ({
        value: option.value,
        label: option?.label || option.value,
      }));
      if (doctype === "User" || doctype === "HD Agent") {
        options.unshift({ label: "@me", value: "@me" });
      }
      return options;
    },
  });
  if (doctype) results.reload();

  const search = useDebounceFn((txt: string) => {
    if (!doctype) return;
    results.update({ params: { txt, doctype, page_length: 10 } });
    results.reload();
  }, 300);

  return { results, search };
}

function buildCondition(
  field: FilterField,
  operator: string,
  value: any
): FilterCondition {
  if (operator.includes("like") && typeof value === "string") {
    value = value.includes("%") ? value : `%${value}%`;
  }
  if (
    field.fieldtype === "Check" &&
    ["equals", "not equals"].includes(operator)
  ) {
    value = value === "Yes" ? true : value === "No" ? false : value;
  }
  return [
    field.fieldname,
    operatorMap[operator.toLowerCase()] || operator,
    value,
  ];
}

function toUiOperator(frappeOperator: string): string {
  return oppositeOperatorMap[String(frappeOperator)] || frappeOperator;
}

function toUiValue(field: FilterField, value: any): any {
  if (field.fieldtype === "Check" && typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return value;
}

function getOperators(fieldtype: string, fieldname?: string) {
  const equality = [
    { label: "Equals", value: "equals" },
    { label: "Not Equals", value: "not equals" },
  ];
  const like = [
    { label: "Like", value: "like" },
    { label: "Not Like", value: "not like" },
  ];
  const inclusion = [
    { label: "In", value: "in" },
    { label: "Not In", value: "not in" },
  ];
  const is = [{ label: "Is", value: "is" }];
  const comparison = [
    { label: "Less Than", value: "<" },
    { label: "Greater Than", value: ">" },
    { label: "Less Than or Equal To", value: "<=" },
    { label: "Greater Than or Equal To", value: ">=" },
  ];

  if (fieldname === "_assign") return [...like, ...is];
  if (typeString.includes(fieldtype) || typeLink.includes(fieldtype)) {
    return [...equality, ...like, ...inclusion, ...is];
  }
  if (typeNumber.includes(fieldtype)) {
    return [...equality, ...like, ...inclusion, ...is, ...comparison];
  }
  if (typeSelect.includes(fieldtype)) return [...equality, ...inclusion, ...is];
  if (typeCheck.includes(fieldtype)) return equality;
  if (fieldtype === "Duration") return [...like, ...inclusion, ...is];
  if (typeDate.includes(fieldtype)) {
    return [
      ...equality,
      ...is,
      ...comparison,
      { label: "Between", value: "between" },
      { label: "Timespan", value: "timespan" },
    ];
  }
  if (typeRating.includes(fieldtype))
    return [...equality, ...is, ...comparison];
  return [...equality, ...like, ...is];
}

function getDefaultOperator(field: FilterField): string {
  if (field.fieldname === "_assign") return "like";
  if (typeDate.includes(field.fieldtype)) return "timespan";
  if (
    typeSelect.includes(field.fieldtype) ||
    typeCheck.includes(field.fieldtype) ||
    typeNumber.includes(field.fieldtype) ||
    typeLink.includes(field.fieldtype) ||
    typeRating.includes(field.fieldtype)
  ) {
    return "equals";
  }
  return "like";
}

function getSelectOptions(options?: string): string[] {
  return (options || "").split("\n").filter((o) => o.trim() !== "");
}

export function fieldIcon(field: FilterField): Component {
  if (["_assign", "owner", "modified_by"].includes(field.fieldname)) {
    return LucideUser;
  }
  const iconMap: Record<string, Component> = {
    Link: LucideLink,
    "Dynamic Link": LucideLink,
    Select: LucideList,
    Date: LucideCalendar,
    Datetime: LucideClock,
    Check: LucideSquareCheck,
    Rating: LucideStar,
    Duration: LucideClock,
    Int: LucideHash,
    Float: LucideHash,
    Currency: LucideHash,
    Percent: LucideHash,
  };
  return iconMap[field.fieldtype] || LucideType;
}

export function filterSummary(filter: ActiveFilter): string {
  const operatorLabels: Record<string, string> = {
    equals: "is",
    "not equals": "is not",
    like: "contains",
    "not like": "doesn't contain",
    in: "in",
    "not in": "not in",
    is: "is",
    between: "between",
    timespan: "in",
    ">": "greater than",
    "<": "less than",
    ">=": "greater than or equal to",
    "<=": "less than or equal to",
  };
  return `${filter.field.label} ${
    operatorLabels[filter.operator] || filter.operator
  } ${displayValue(filter)}`;
}

function displayValue(filter: ActiveFilter): string {
  const value = filter.value;
  // ratings are stored as a 0..1 fraction; show numeric ones as star counts
  // (×5). "is" uses set / not set, so leave those (and any non-numeric) alone.
  if (filter.field.fieldtype === "Rating" && filter.operator !== "is") {
    const toStars = (v: any) => {
      const n = Number(v);
      return Number.isFinite(n) ? String(Math.round(n * 5)) : String(v ?? "");
    };
    return Array.isArray(value) ? value.map(toStars).join(", ") : toStars(value);
  }
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "string") return value.replaceAll("%", "");
  return String(value ?? "");
}

const operatorMap: Record<string, string> = {
  is: "is",
  "is not": "is not",
  in: "in",
  "not in": "not in",
  equals: "=",
  "not equals": "!=",
  like: "LIKE",
  "not like": "NOT LIKE",
  ">": ">",
  "<": "<",
  ">=": ">=",
  "<=": "<=",
  between: "between",
  timespan: "timespan",
};

const oppositeOperatorMap: Record<string, string> = Object.fromEntries(
  Object.entries(operatorMap).map(([ui, frappe]) => [frappe, ui])
);

const timespanOptions = [
  { label: "Today", value: "today" },
  { label: "Yesterday", value: "yesterday" },
  { label: "Tomorrow", value: "tomorrow" },
  { label: "Last 7 Days", value: "last 7 days" },
  { label: "Last 14 Days", value: "last 14 days" },
  { label: "Last 30 Days", value: "last 30 days" },
  { label: "Last 90 Days", value: "last 90 days" },
  { label: "Last Week", value: "last week" },
  { label: "Last Month", value: "last month" },
  { label: "Last Quarter", value: "last quarter" },
  { label: "Last 6 Months", value: "last 6 months" },
  { label: "Last Year", value: "last year" },
  { label: "This Week", value: "this week" },
  { label: "This Month", value: "this month" },
  { label: "This Quarter", value: "this quarter" },
  { label: "This Year", value: "this year" },
  { label: "Next Week", value: "next week" },
  { label: "Next Month", value: "next month" },
  { label: "Next Quarter", value: "next quarter" },
  { label: "Next 6 Months", value: "next 6 months" },
  { label: "Next Year", value: "next year" },
  { label: "Next 7 Days", value: "next 7 days" },
  { label: "Next 14 Days", value: "next 14 days" },
  { label: "Next 30 Days", value: "next 30 days" },
];
