import { computed, ComputedRef } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

type TicketPriority = {
  name: string;
  description: string;
};

export const useTicketPriorityStore = defineStore("ticketPriority", () => {
  const d__ = createListResource({
    doctype: "HD Ticket Priority",
    orderBy: "integer_value desc",
    auto: true,
    pageLength: 99999,
  });

  const options: ComputedRef<Array<TicketPriority>> = computed(
    () => d__.list?.data || []
  );
  const dropdown = computed(() =>
    options.value.map((o) => ({
      label: o.name,
      value: o.name,
    }))
  );
  const names = computed(() => options.value.map((o) => o.name));
  const colorMap = {
    Urgent: "red",
    High: "orange",
    Medium: "blue",
    Low: "green",
  };

  return {
    colorMap,
    dropdown,
    names,
    options,
  };
});
