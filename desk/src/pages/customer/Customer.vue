<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="-ml-[2px]" />
      </template>
    </LayoutHeader>
    <div
      class="gap-5 flex flex-col overscroll-none overflow-hidden h-full"
      v-if="!customer.loading && customer.doc"
    >
      <!-- customer detail -->
      <CustomerInfo />
      <!-- Tabs -->
      <Tabs v-model="activeTab" :tabs="tabs">
        <template #tab-item="{ tab, selected }">
          <button
            class="group flex items-center gap-2 border-b border-transparent py-2 text-base text-ink-gray-5 duration-300 ease-in-out hover:text-ink-gray-9"
            :class="{ 'text-ink-gray-9': selected }"
          >
            <component :is="tab.icon" v-if="tab.icon" class="h-5" />
            {{ __(tab.label) }}
            <Badge
              class="group-hover:bg-surface-gray-7"
              :class="[selected ? '!bg-surface-gray-7' : '!bg-gray-600']"
              variant="solid"
              theme="gray"
              size="sm"
            >
              {{ tab.count }}
            </Badge>
          </button>
        </template>
        <template #tab-panel="{ tab }">
          <div class="p-5 overflow-hidden">
            <div v-if="tab.label === __('Tickets')">
              <!-- Tickets tab content -->
              <CustomerTicketsTab />
            </div>
            <CustomerContactTab v-if="tab.label === __('Contacts')" />
          </div>
        </template>
      </Tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import CustomerContactTab from "@/components/customer/CustomerContactTab.vue";
import CustomerTicketsTab from "@/components/customer/CustomerTicketsTab.vue";
import TicketHashIcon from "@/components/icons/TicketHashIcon.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { useCustomer } from "@/composables/customer";
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import { Badge, Breadcrumbs, Tabs, usePageMeta } from "frappe-ui";
import { computed, h, onMounted, provide } from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideSquareUser from "~icons/lucide/square-user";
import CustomerInfo from "./CustomerInfo.vue";
import { ticketsListResource } from "./tickets";
// props with type set at string
const props = defineProps<{
  id: string;
}>();

const route = useRoute();
const router = useRouter();

const tabs = computed(() => [
  {
    label: __("Tickets"),
    hash: "tickets",
    count: ticketsListResource.data?.length ?? 0,
    icon: h(TicketHashIcon, { class: "size-4" }),
  },
  {
    label: __("Contacts"),
    hash: "contacts",
    count: customer.getContacts.loading
      ? 0
      : customer.getContacts.data?.length ?? 0,
    icon: h(LucideSquareUser, { class: "size-4" }),
  },
]);
const { doc: customer } = useCustomer(props.id);

provide(CustomerResourceSymbol, customer);

const activeTab = computed<number>({
  get() {
    const index = tabs.value.findIndex((t) => t.hash === route.hash.slice(1));
    if (index === -1) {
      router.replace({ hash: "" });
      return 0;
    }
    return index;
  },
  set(i) {
    if (i === 0) {
      router.replace({ hash: "" });
      return;
    }
    router.replace({ hash: `#${tabs.value[i].hash}` });
  },
});

const breadcrumbs = [
  {
    label: __("Customers"),
    route: { name: "CustomerList" },
  },
  {
    label: props.id,
  },
];

onMounted(() => {
  customer.getPendingInvites.fetch();
  customer.getContacts.fetch();
  ticketsListResource.fetch();
});

usePageMeta(() => {
  return {
    title: props.id,
  };
});
</script>
