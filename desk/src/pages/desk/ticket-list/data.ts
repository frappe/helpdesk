import { ref } from "vue";
import { defineStore } from "pinia";
import { useKeymapStore } from "@/stores/keymap";
import { createListManager } from "@/composables/listManager";

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

  const tickets = createListManager({
    doctype: "HD Ticket",
    pageLength: 20,
    auto: true,
  });

  return {
    deinit,
    init,
    selection,
    tickets,
  };
});
