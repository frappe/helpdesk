import { ref, watchEffect, Ref } from "vue";
import { useRoute, useRouter, RouteLocationNamedRaw } from "vue-router";
import { toValue } from "@vueuse/core";
import { DocField, Filter } from "@/types";
import { useAuthStore } from "@/stores/auth";

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

export function useFilter(fields?: DocField[] | Ref<DocField[]>) {
  const route = useRoute();
  const router = useRouter();
  const { userId } = useAuthStore();
  const storage = ref(new Set<Filter>());

  watchEffect(() => {
    const f__ = toValue(fields);
    if (fields && !f__) return;
    storage.value = new Set();
    const q = (route.query.q as string) || "";
    q.split(" ")
      .map((f) => {
        const [fieldname, operator, value] = f
          .split(":")
          .map(decodeURIComponent);
        const field = (f__ || []).find((f) => f.fieldname === fieldname);
        return {
          field,
          fieldname,
          operator,
          value,
        };
      })
      .filter((f) => !f__ || (f__ && f.field))
      .filter((f) => operatorMap[f.operator])
      .forEach((f) => storage.value.add(f));
  });

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

  return { apply, getArgs, storage };
}
