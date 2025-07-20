import { createListResource } from "frappe-ui";
import { computed } from "vue";

export const fieldDependenciesList = createListResource({
  doctype: "HD Form Script",
  filters: { is_standard: 1, name: ["like", "%Field Dependency%"] },
  fields: ["name", "enabled", "owner"],
  auto: true,
  cache: ["FD", "List"],
});

export const hiddenChildFields = computed(() => {
  let _fields = [];
  fieldDependenciesList.data?.forEach((item) => {
    let [_, parent, child] = item.name.split("-");
    if (parent && child) {
      _fields.push(child);
      _fields.push(parent);
    }
  });
  return _fields;
});
