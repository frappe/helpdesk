<template>
  <div class="flex flex-col overflow-y-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="-ml-[2px]" />
      </template>
    </LayoutHeader>
    <div
      class="gap-5 flex flex-col h-full"
      v-if="customer.doc && customer.doc?.name"
    >
      <!-- customer detail -->
      <PageInfo
        :avatar="{
          label: customer.doc.customer_name ?? '',
          image: customer.doc.image,
          shape: 'square',
        }"
        :docInfo="customerInfo"
      >
        <template #actions>
          <Button
            v-if="hasPermission()"
            variant="subtle"
            @click="customerDialog = true"
          >
            <div class="flex gap-1 items-center">
              <LucideSquarePen class="h-4 w-4" />
              <span>{{ __("Edit") }}</span>
            </div>
          </Button>
        </template>
      </PageInfo>
      <div class="overflow-y-auto flex-1">
        <TicketStats
          :dt="'HD Customer'"
          :dn="customer.doc.name"
          v-if="!isMobileView"
        />
        <!-- Tabs -->
        <Tabs v-model="activeTab" :tabs="tabs" class="tabs-sticky-header">
          <template #tab-item="{ tab, selected }">
            <button
              class="group flex items-center gap-2 border-b border-transparent py-2 text-base text-ink-gray-5 duration-300 ease-in-out hover:text-ink-gray-9"
              :class="{ 'text-ink-gray-9': selected }"
            >
              <component :is="tab.icon" v-if="tab.icon" class="h-5" />
              {{ __(tab.label) }}
              <Badge
                class="group-hover:bg-surface-gray-7"
                :class="[
                  selected
                    ? '!bg-surface-gray-7'
                    : '!bg-surface-gray-2 !text-ink-gray-7',
                ]"
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
                <TicketsTab
                  :doc="customer"
                  :ticketsListResource="ticketsListResource"
                  :baseFilter="{ customer: props.id }"
                  :additionalFilter="{
                    key: 'contact',
                    placeholder: __('Contact'),
                    doctype: 'Contact',
                    filters: customer.getContacts.data?.length
                      ? { name: ['in', customer.getContacts.data.map((c: { contact_name: string }) => c.contact_name)] }
                      : undefined,
                  }"
                />
              </div>
              <CustomerContactTab v-if="tab.label === __('Contacts')" />
            </div>
          </template>
        </Tabs>
      </div>
    </div>
  </div>
  <EditCustomerDialog
    v-if="customerDialog"
    v-model="customerDialog"
    @update="customerDialog = false"
    :id="id"
  />
</template>

<script setup lang="ts">
import CustomerContactTab from "@/components/customer/CustomerContactTab.vue";
import TicketsTab from "@/components/customer/TicketsTab.vue";
import TicketStats from "@/components/customer/TicketStats.vue";
import TicketHashIcon from "@/components/icons/TicketHashIcon.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import PageInfo from "@/components/PageInfo.vue";
import { useCustomer } from "@/composables/customer";
import { useScreenSize } from "@/composables/screen";
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import { hasPermission } from "@/utils";
import { Badge, Breadcrumbs, Button, Tabs, usePageMeta } from "frappe-ui";
import { computed, h, markRaw, onMounted, provide, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideGlobe from "~icons/lucide/globe";
import LucideMail from "~icons/lucide/mail";
import LucideMapPin from "~icons/lucide/map-pin";
import LucidePhone from "~icons/lucide/phone";
import LucideSquarePen from "~icons/lucide/square-pen";
import LucideSquareUser from "~icons/lucide/square-user";
import { getTicketListResource } from "../../stores/docTickets";
// props with type set at string
const props = defineProps<{
  id: string;
}>();
const route = useRoute();
const router = useRouter();

const { isMobileView } = useScreenSize();
const { ticketsListResource } = getTicketListResource();

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

const customerDialog = ref(false);

const customerInfo = computed(() => [
  {
    icon: markRaw(LucideGlobe),
    value: customer.doc.domain,
    condition: !!customer.doc.domain,
  },
  {
    icon: markRaw(LucideMail),
    value: customer.doc.email_id,
    condition: !!customer.doc.email_id,
  },
  {
    icon: markRaw(LucidePhone),
    value: customer.doc.mobile_no,
    condition: !!customer.doc.mobile_no,
  },
  {
    icon: markRaw(LucideMapPin),
    value: customer.doc.country,
    condition: !!customer.doc.country,
  },
]);

onMounted(() => {
  customer.getPendingInvites.fetch();
  customer.getContacts.fetch();
  ticketsListResource.update({
    filters: {
      customer: props.id,
    },
  });
  ticketsListResource.fetch();
});

usePageMeta(() => {
  return {
    title: `Customer: ${props.id}`,
  };
});
</script>

<style scoped>
.tabs-sticky-header :deep([role="tablist"]) {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: white;
}
</style>
