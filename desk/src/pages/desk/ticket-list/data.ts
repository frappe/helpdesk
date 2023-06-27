import { ref } from "vue";
import { defineStore } from "pinia";
import { createResource } from "frappe-ui";
import { useKeymapStore } from "@/stores/keymap";

export const useTicketListStore = defineStore("ticketList", () => {
  const KEYMAPS = [
    {
      button: "R",
      status: "Replied",
    },
    {
      button: "E",
      status: "Resolved",
    },
    {
      button: "C",
      status: "Closed",
    },
  ];
  const KEYMAP_PREFIX = "Control";
  const keymapStore = useKeymapStore();
  const selection = ref(new Set<string>());
  const limit = ref(20);
  const start = ref(1);

  function init() {
    KEYMAPS.forEach((o) => {
      keymapStore.add(
        [KEYMAP_PREFIX, o.button],
        () => {
          selection.value.forEach((ticketId) => {
            tickets.setValue.submit({
              name: ticketId,
              status: o.status,
            });
          });
        },
        `Mark ticket as ${o.status.toLowerCase()}`
      );
    });
  }

  function deinit() {
    KEYMAPS.forEach((o) => keymapStore.remove([KEYMAP_PREFIX, o.button]));
  }

  const tickets = createResource({
    url: "helpdesk.api.ticket.get_many",
    auto: true,
    params: {
      start: start.value,
      limit: limit.value,
    },
  });

  tickets.previous = () => {
    const __s = start.value - limit.value;
    start.value = __s > 0 ? __s : 1;
    tickets.update({
      params: {
        start: start.value,
        limit: limit.value,
      },
    });
    tickets.reload();
  };

  tickets.next = () => {
    start.value = start.value + limit.value;
    tickets.update({
      params: {
        start: start.value,
        limit: limit.value,
      },
    });
    tickets.reload();
  };

  return {
    deinit,
    init,
    limit,
    selection,
    start,
    tickets,
  };
});
