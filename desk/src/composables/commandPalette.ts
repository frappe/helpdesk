import { markRaw, reactive, h, ref } from "vue";
import { useRouter } from "vue-router";
import { CommandPaletteItem } from "frappe-ui";
import LucideBookOpen from "~icons/lucide/book-open";
import LucideLayoutGrid from "~icons/lucide/layout-grid";
import LucideTicket from "~icons/lucide/ticket";
import LucideUser from "~icons/lucide/user";
import { watch } from "vue";

// function search(searchTerm) {
//   return commandPalette.commands.filter((command) => {
//     return command.title.toLowerCase().includes(searchTerm.toLowerCase());
//   });
// }

export default function useCommandPalette() {
  const router = useRouter();
  // const show = ref(true); // TODO: use ref
  const show = true;
  const query = ref("");
  const result = [
    {
      title: "Navigation",
      component: CommandPaletteItem,
      items: [
        {
          title: "Tickets",
          icon: () => h(LucideTicket),
          action: () => router.push("/tickets"),
        },
        {
          title: "Dashboard",
          icon: () => h(LucideLayoutGrid),
          action: () => router.push("/dashboard"),
        },
        {
          title: "Agents",
          icon: () => h(LucideUser),
          action: () => router.push("/agents"),
        },
        {
          title: "Knowledge Base",
          icon: () => h(LucideBookOpen),
          action: () => router.push("/knowledge-base"),
        },
      ],
    },
  ];

  // const open = () => (show.value = true);
  // const close = () => (show.value = false);
  const close = () => ({});

  // watch(query, (q) => {
  //   debugger;
  // });

  return {
    show,
    query,
    result,
    open,
    close,
  };
}
