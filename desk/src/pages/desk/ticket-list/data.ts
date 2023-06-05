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

  function init() {
    KEYMAPS.forEach((o) => {
      keymapStore.add(
        [KEYMAP_PREFIX, o.button],
        () => {
          selected.value.forEach((ticketId) => {
            tickets.setValue.submit({
              name: ticketId,
              status: o.status,
            });
          });
        },
        `Set ticket as ${o.status.toLowerCase()}`
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
    init,
    deinit,
    tickets,
  };
});
