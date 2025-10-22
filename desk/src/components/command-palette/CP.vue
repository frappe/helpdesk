<template>
  <Dialog v-model="show" :options="{ size: 'xl', position: 'top' }">
    <template #body>
      <div>
        <Combobox nullable @update:model-value="onSelection">
          <div class="relative">
            <div class="pl-4.5 absolute inset-y-0 left-0 flex items-center">
              <LucideSearch class="h-4 w-4" />
            </div>
            <ComboboxInput
              placeholder="Search tickets, emails, comments, or #234 to navigate to ticket"
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
              v-for="group in groupedSearchResults"
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
<script setup>
import { isCustomerPortal } from "@/utils";
import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from "@headlessui/vue";
import { useDevice } from "@/composables";
import { useShortcut } from "@/composables/shortcuts";

import { Dialog } from "frappe-ui";
import { computed, h, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import LucideBookOpen from "~icons/lucide/book-open";
import LucideTicket from "~icons/lucide/ticket";
import CPGroup from "./CPGroup.vue";
const router = useRouter();
const { isMac } = useDevice();

// Reactive data
const show = defineModel();
const query = ref("");

// Computed properties
const navigationItems = computed(() => {
  const items = [];
  if (query.value.startsWith("#")) {
    items.push({
      title: `Go to Ticket #${query.value.slice(1)}`,
      icon: () => h(LucideTicket),
      route: {
        name: "TicketAgent",
        params: { ticketId: query.value.slice(1) },
      },
    });
  } else {
    items.push({
      title: "Tickets",
      icon: () => h(LucideTicket),
      route: { name: "TicketsAgent" },
    });
  }
  items.push({
    title: "Knowledge Base",
    icon: () => h(LucideBookOpen),
    route: {
      name: isCustomerPortal.value
        ? "CustomerKnowledgeBase"
        : "AgentKnowledgeBase",
    },
  });

  return {
    title: "Jump to",
    component: h(CPGroup),
    items,
  };
});

const fullSearchItem = computed(() => ({
  title: "Search",
  hideTitle: true,
  component: h(CPGroup),
  items: [
    {
      title: `Search for "${query.value}"`,
      icon: () => h(LucideFileSearch),
      route: { name: "SearchAgent", query: { q: query.value } },
    },
  ],
}));

const groupedSearchResults = computed(() => {
  let results = [navigationItems.value];

  // Add search option if there's a query and we're not in customer portal
  if (query.value.length > 2 && !isCustomerPortal.value) {
    results.push(fullSearchItem.value);
  }

  return results;
});

// Methods
const onInput = (e) => {
  query.value = e.target.value;
};

const onSelection = (value) => {
  if (value) {
    router.push(value.route);
    hideCommandPalette();
  }
};

const addKeyboardShortcut = () => {
  useShortcut({ key: "k", meta: true }, toggleCommandPalette);
};

function hideCommandPalette() {
  show.value = false;
}

function toggleCommandPalette() {
  show.value = !show.value;
}

// Watchers
watch(show, (value) => {
  if (value) {
    query.value = "";
  }
});

// Lifecycle hooks
onMounted(() => {
  if (isCustomerPortal.value) return;
  addKeyboardShortcut();
});

onBeforeUnmount(() => {
  hideCommandPalette();
});
</script>
