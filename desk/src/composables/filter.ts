import { ref, watchEffect, Ref } from "vue";
import { useRoute } from "vue-router";
import { toValue } from "@vueuse/core";
import { DocField, Filter } from "@/types";

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
  const storage = ref(new Set<Filter>());

  watchEffect(() => {
    const f__ = toValue(fields);
    if (fields && !f__) return;
    storage.value = new Set();
    const q = (route.query.q as string) || "";
    q.split(" ")
      .map((f) => {
        const [fieldname, operator, value] = f.split(":");
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
    const obj = l__.reduce((p, c) => {
      p[c.fieldname] = [operatorMap[c.operator.toLowerCase()], c.value];
      return p;
    }, {});
    const merged = { ...old, ...obj };
    return merged;
  }

  return { getArgs, storage };
}
