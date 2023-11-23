import { watchEffect } from "vue";
import { useRoute, useRouter, RouteLocationNamedRaw } from "vue-router";
import { useStorage } from "@vueuse/core";
import { createResource } from "frappe-ui";
import { orderBy } from "lodash";
import { DocField, Filter, Resource } from "@/types";
import { useAuthStore } from "@/stores/auth";

const storagePrefix = "filters_";
const operatorMap = {
  is: "=",
  "is not": "!=",
  equals: "=",
  "not equals": "!=",
  yes: true,
  no: false,
  like: "LIKE",
  "not like": "NOT LIKE",
  ">": ">",
  "<": "<",
  ">=": ">=",
  "<=": "<=",
};

export function useFilter(doctype: string) {
  const route = useRoute();
  const router = useRouter();
  const { userId } = useAuthStore();
  const storage = useStorage(
    storagePrefix + route.name.toString(),
    new Set<Filter>()
  );

  const fields: Resource<Array<DocField>> = createResource({
    url: "helpdesk.api.doc.get_filterable_fields",
    cache: ["DocField", doctype],
    auto: !!doctype,
    params: {
      doctype,
      append_assign: true,
    },
    transform: (data) => {
      data = orderBy(
        data.map((f) => ({
          label: f.label,
          value: f.fieldname,
          ...f,
        })),
        "label"
      );
      return data;
    },
  });

  watchEffect(() => {
    if (!fields.data) return;
    const q = route.query.q as string;
    if (q) {
      storage.value = new Set(fromUrl(q, fields.data));
    }
  });

  function fromUrl(query: string, fields: DocField[]) {
    return query
      .split(" ")
      .map((f) => {
        const [fieldname, operator, value] = f
          .split(":")
          .map(decodeURIComponent);
        const field = (fields || []).find((f) => f.fieldname === fieldname);
        return {
          field,
          fieldname,
          operator,
          value,
        };
      })
      .filter((f) => !fields || (fields && f.field))
      .filter((f) => operatorMap[f.operator]);
  }

  function getArgs(old?: Record<string, string | string[]>) {
    old = old || {};
    const l__ = Array.from(storage.value);
    const obj = l__.map(transformIn).reduce((p, c) => {
      p[c.fieldname] = [operatorMap[c.operator.toLowerCase()], c.value];
      return p;
    }, {});
    const merged = { ...old, ...obj };
    return merged;
  }

  function add(f: Filter) {
    storage.value.forEach((i) => {
      if (i.fieldname === f.fieldname) {
        storage.value.delete(i);
      }
    });
    storage.value.add(f);
  }

  function apply(r?: RouteLocationNamedRaw) {
    r = r || route;
    const l__ = Array.from(storage.value);
    const q = l__
      .map(transformOut)
      .map((f) =>
        [f.fieldname, f.operator.toLowerCase(), f.value]
          .map(encodeURIComponent)
          .join(":")
      )
      .join(" ");
    router.push({
      ...r,
      query: {
        ...r.query,
        q,
      },
    });
  }

  /**
   * Used to set fields internally. These will not reflect in URL.
   * Can be used for APIs
   */
  function transformIn(f: Filter) {
    if (f.fieldname === "_assign") {
      f.operator = f.operator === "is" ? "like" : "not like";
    }
    if (f.operator.includes("like")) {
      f.value = `%${f.value}%`;
    }
    return f;
  }

  /**
   * Used to set fields in URL query
   */
  function transformOut(f: Filter) {
    if (f.value === "@me") {
      f.value = userId;
    }
    return f;
  }

  return {
    add,
    apply,
    fields,
    getArgs,
    storage,
  };
}
