import { ref, watch } from "vue";
import { createListResource, createResource } from "frappe-ui";

const GET_LIST_METHOD = "helpdesk.extends.client.get_list";
const GET_LIST_META_METHOD = "helpdesk.extends.client.get_list_meta";

type ListOptions = {
  doctype: string;
  fields?: Array<string>;
  filters?: object;
  orderBy?: string;
  pageLength?: number;
  start?: number;
  cache?: boolean | string | Array<string>;
  auto?: boolean;
  transform?: any;
};

type MetaData = {
  total_count: number;
  total_pages: number;
  current_page: number;
  start_from: number;
  end_at: number;
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
  const auto = options.auto;
  const transform = options.transform;

  const list = createListResource({
    type: "list",
    url: GET_LIST_METHOD,
    realtime: true,
    doctype,
    fields,
    orderBy,
    filters,
    pageLength,
    start,
    cache,
    auto,
    transform,
    onSuccess() {
      meta.submit({
        doctype,
        filters: list.filters,
        limit: list.pageLength,
        order_by: list.orderBy,
        start: list.start,
      });
    },
  });

  Object.assign(list, {
    totalCount: ref(0),
    totalPages: ref(0),
    currentPage: ref(0),
    hasNextPage: ref(false),
    hasPreviousPage: ref(false),
    startFrom: ref(0),
    endAt: ref(0),
  });

  const meta = createResource({
    url: GET_LIST_META_METHOD,
    onSuccess: (data: MetaData) => {
      list.totalCount = data.total_count;
      list.totalPages = data.total_pages;
      list.currentPage = data.current_page;
      list.hasNextPage = data.has_next_page;
      list.hasPreviousPage = data.has_previous_page;
      list.startFrom = data.start_from;
      list.endAt = data.end_at;
    },
  });

  watch(
    () => list.list.loading,
    () => {
      list.hasPreviousPage = false;
      list.hasNextPage = false;
    }
  );

  return list;
}
