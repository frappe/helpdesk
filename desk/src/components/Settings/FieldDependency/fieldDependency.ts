import { call, createListResource } from "frappe-ui";
import { computed, reactive } from "vue";

export const fieldDependenciesList = createListResource({
  doctype: "HD Form Script",
  filters: { is_standard: 1, name: ["like", "%Field Dependency%"] },
  fields: ["name", "enabled", "owner"],
  auto: true,
  cache: ["FD", "List"],
  orderBy: "modified desc",
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

const optionsMap = reactive({});

export async function getFieldOptions(field: any): Promise<string[]> {
  if (optionsMap[field.value]) {
    return optionsMap[field.value];
  }

  if (field.type === "Select") {
    optionsMap[field.value] = field.options.split("\n");
    return optionsMap[field.value];
  } else if (field.type === "Link") {
    let options = await call("frappe.client.get_list", {
      doctype: field.options,
      fields: ["name"],
      limit_page_length: 999,
    });
    optionsMap[field.value] = options.map((o) => o.name);
    return optionsMap[field.value];
  }
}
