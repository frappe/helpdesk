import { computed } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

export const useCustomerStore = defineStore("customer", () => {
  const customer = createListResource({
    doctype: "HD Customer",
    fields: ["name", "customer_name", "domain", "image"],
    auto: true,
    pageLength: 99999,
  });

  const dropdown = computed(() =>
    customer.data?.map((o) => ({
      label: o.customer_name,
      value: o.name,
    }))
  );

  return {
    dropdown,
    customer,
  };
});
