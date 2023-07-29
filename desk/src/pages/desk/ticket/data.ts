import { reactive, ref } from "vue";
import { defineStore } from "pinia";
import { emitter } from "@/emitter";

export const useTicketStore = defineStore("ticket", () => {
  const sidebar = reactive({
    isExpanded: true,
  });
  const doc = ref({});
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
    doc.value = {};
  }

  emitter.on("ticket:focus", (id: string) => scrollTo(id));

  return {
    $reset,
    doc,
    editor,
    sidebar,
  };
});
