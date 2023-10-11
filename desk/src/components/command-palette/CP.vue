<template>
  <Dialog
    v-model="show"
    :options="{ size: 'xl', position: 'top' }"
    @after-leave="filteredOptions = []"
  >
    <template #body>
      <div>
        <Combobox
          v-slot="{ activeIndex }"
          nullable
          @update:model-value="onSelection"
        >
          <div class="relative">
            <div class="pl-4.5 absolute inset-y-0 left-0 flex items-center">
              <LucideSearch class="h-4 w-4" />
            </div>
            <ComboboxInput
              placeholder="Search"
              class="pl-11.5 pr-4.5 w-full border-none bg-transparent py-3 text-base text-gray-800 placeholder:text-gray-500 focus:ring-0"
              autocomplete="off"
              @input="onInput"
            />
          </div>
          <ComboboxOptions
            class="max-h-96 overflow-auto border-t border-gray-100"
            static
            :hold="true"
          >
            <div
              v-for="(group, index) in groupedSearchResults"
              :key="group.title"
              class="mt-4.5 mb-2 first:mt-3"
            >
              <div
                v-if="!group.hideTitle"
                class="px-4.5 mb-2.5 text-base text-gray-600"
              >
                {{ group.title }}
              </div>
              <ComboboxOption
                v-for="item in group.items"
                :key="`${item.doctype}:${item.name}`"
                v-slot="{ active }"
                :value="item"
                class="px-2.5"
                :disabled="item.disabled"
              >
                <component
                  :is="group.component"
                  :item="item"
                  :active="active"
                />
              </ComboboxOption>
            </div>
          </ComboboxOptions>
        </Combobox>
      </div>
    </template>
  </Dialog>
</template>
<script>
import { h, ref } from "vue";
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from "@headlessui/vue";
import CPItem from "./CPItem.vue";
import CPTicket from "./CPTicket.vue";
import LucideLayoutGrid from "~icons/lucide/layout-grid";
import LucideSearch from "~icons/lucide/file-search";
import LucideTicket from "~icons/lucide/ticket";
import LucideUser from "~icons/lucide/user";

let show = ref(false);

export function showCommandPalette() {
  show.value = true;
}

export function hideCommandPalette() {
  show.value = false;
}

export function toggleCommandPalette() {
  show.value = !show.value;
}

export default {
  name: "CommandPalette",
  components: {
    Combobox,
    ComboboxInput,
    ComboboxOptions,
    ComboboxOption,
    CPTicket,
    CPItem,
  },
  setup() {
    return { show };
  },
  data() {
    return {
      query: "",
      filteredOptions: [],
    };
  },
  resources: {
    search() {
      return {
        url: "helpdesk.search.search",
        makeParams(query) {
          return { query };
        },
        debounce: 300,
        transform(groups) {
          for (let group of groups) {
            if (group.title === "Tickets") {
              group.component = "CPTicket";
              group.items = group.items.map((item) => {
                item.route = {
                  name: "TicketAgent",
                  params: {
                    ticketId: item.name,
                  },
                };
                return item;
              });
            }
          }
          return groups;
        },
      };
    },
  },
  computed: {
    navigationItems() {
      return {
        title: "Jump to",
        component: "CPItem",
        items: [
          {
            title: "Tickets",
            icon: () => h(LucideTicket),
            route: { name: "TicketsAgent" },
          },
          {
            title: "Dashboard",
            icon: () => h(LucideLayoutGrid),
            route: { name: "DeskDashboard" },
            condition: () => true,
          },
          {
            title: "Agents",
            icon: () => h(LucideUser),
            route: { name: "AgentList" },
            condition: () => true,
          },
        ].filter((item) => (item.condition ? item.condition() : true)),
      };
    },
    fullSearchItem() {
      return {
        title: "Search",
        hideTitle: true,
        component: "CPItem",
        items: [
          {
            title: `Search for "${this.query}"`,
            icon: () => h(LucideSearch),
            route: { name: "Search", query: { q: this.query } },
          },
        ],
      };
    },
    groupedSearchResults() {
      let groups = [{ title: "Tickets", component: "CPTicket" }];
      let itemsByGroup = {};
      for (const group of groups) {
        itemsByGroup[group.title] = [];
      }
      for (const item of this.filteredOptions) {
        itemsByGroup[item.group].push(item);
      }
      let localResults = groups
        .map((group) => {
          return {
            ...group,
            items: itemsByGroup[group.title],
          };
        })
        .filter((group) => group.items.length > 0);

      let serverResults =
        this.query.length > 2 && this.$resources.search.data
          ? this.$resources.search.data
          : [];
      let results = [...localResults, ...serverResults];
      return [
        ...(results.length === 0 ? [this.navigationItems] : []),
        ...results,
      ];
    },
  },
  watch: {
    show(value) {
      if (value) {
        this.query = "";
      }
    },
  },
  mounted() {
    this.addKeyboardShortcut();
  },
  beforeUnmount() {
    hideCommandPalette();
  },
  methods: {
    onInput(e) {
      this.query = e.target.value;
      if (this.query && this.query.length > 2) {
        this.$resources.search.submit(this.query);
      } else {
        this.filteredOptions = [];
      }
    },
    onSelection(value) {
      if (value) {
        this.$router.push(value.route);
        hideCommandPalette();
      }
    },
    addKeyboardShortcut() {
      window.addEventListener("keydown", (e) => {
        if (
          e.key === "k" &&
          (e.ctrlKey || e.metaKey) &&
          !e.target.classList?.contains("ProseMirror")
        ) {
          toggleCommandPalette();
          e.preventDefault();
        }
      });
    },
  },
};
</script>
