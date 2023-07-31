import { Ref, reactive, ref } from "vue";
import { defineStore } from "pinia";
import { createResource } from "frappe-ui";
import { emitter } from "@/emitter";
import { Resource, Ticket } from "@/types";

const ticket: Ref<Resource<Ticket>> = ref(null);
export function useTicket(id?: number | string) {
  if (!ticket.value && id) {
    const t = createResource({
      url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
      params: {
        name: id,
      },
      auto: true,
    });
    ticket.value = t;
  }

  return ticket;
}

export const useTicketStore = defineStore("ticket", () => {
  const sidebar = reactive({
    isExpanded: true,
  });
  const editor = reactive({
    isExpanded: false,
    content: "",
    attachments: [],
    cc: [],
    bcc: [],
    isCcVisible: false,
    isBccVisible: false,
    tiptap: null,
    clean: () => {
      editor.isExpanded = false;
      editor.content = "";
      editor.attachments = [];
      editor.cc = [];
      editor.bcc = [];
      editor.isCcVisible = false;
      editor.isBccVisible = false;
      sidebar.isExpanded = true;
    },
  });

  function scrollTo(id: string) {
    const cls = "animate-pulse";
    const e = document.getElementById(id);
    e.scrollIntoView({ behavior: "smooth" });
    e.classList.add(cls);
    setTimeout(() => e.classList.remove(cls), 2000);
  }

  function $reset() {
    editor.clean();
  }

  emitter.on("ticket:focus", (id: string) => scrollTo(id));

  return {
    $reset,
    editor,
    sidebar,
  };
});
