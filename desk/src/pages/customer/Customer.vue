<template>
  <div
    class="flex h-full flex-col overflow-y-hidden max-w-screen-xl mx-auto w-full"
  >
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="-ml-[2px]" />
      </template>
    </LayoutHeader>
    <div
      class="gap-5 flex flex-col flex-1 min-h-0"
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
          <div v-if="hasPermission()" class="flex gap-2 items-center">
            <Button variant="subtle" @click="customerDialog = true">
              <div class="flex gap-1 items-center">
                <LucideSquarePen class="h-4 w-4" />
                <span>{{ __("Edit") }}</span>
              </div>
            </Button>
            <Dropdown :options="dropdownActions" placement="right">
              <Button icon="more-horizontal" variant="subtle" />
            </Dropdown>
          </div>
        </template>
      </PageInfo>
      <div class="overflow-y-auto overscroll-y-contain flex-1 flex flex-col">
        <TicketStats
          :dt="'HD Customer'"
          :dn="customer.doc.name"
          v-if="!isMobileView"
        />
        <!-- Tabs -->
        <Tabs
          v-model="activeTab"
          :tabs="tabs"
          class="tabs-sticky-header [&_[role='tablist']]:!bg-surface-base"
        >
          <template #tab-item="{ tab, selected }">
            <button
              class="group flex items-center gap-2 border-b border-transparent py-2 text-base text-ink-gray-5 duration-300 ease-in-out hover:text-ink-gray-9"
              :class="{ 'text-ink-gray-9': selected }"
            >
              <component :is="tab.icon" v-if="tab.icon" class="h-5" />
              {{ __(tab.label) }}
              <Badge
                class="group-hover:bg-surface-gray-10 !bg-surface-gray-2 !text-ink-gray-7"
                variant="solid"
                theme="gray"
                size="sm"
              >
                {{ tab.count }}
              </Badge>
            </button>
          </template>
          <template #tab-panel="{ tab }">
            <div class="p-5 flex flex-col flex-1 min-h-0">
              <div v-if="tab.label === __('Tickets')">
                <!-- Tickets tab content -->
                <TicketsTab
                  :ticketsListResource="ticketsListResource"
                  :ticketsCountResource="ticketsCountResource"
                  :baseFilter="{ customer: props.id }"
                  :additionalFilter="contactFilter"
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
  <DeleteWithTicketsDialog
    v-model="showDeleteDialog"
    :name="id"
    link-field="customer"
    :title="__('Delete Contact')"
    :message="
      __(
        'Are you sure you want to delete this customer? The reference to this customer will be removed from all the related tickets.'
      )
    "
    :on-delete="handleDelete"
  />
</template>

<script setup lang="ts">
import CustomerContactTab from "@/components/customer/CustomerContactTab.vue";
import TicketsTab from "@/components/customer/TicketsTab.vue";
import TicketStats from "@/components/customer/TicketStats.vue";
import DeleteWithTicketsDialog from "@/components/DeleteWithTicketsDialog.vue";
import TicketHashIcon from "@/components/icons/TicketHashIcon.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import PageInfo from "@/components/PageInfo.vue";
import { useCustomer } from "@/composables/customer";
import { useScreenSize } from "@/composables/screen";
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import { hasPermission } from "@/utils";
import {
  Badge,
  Breadcrumbs,
  Button,
  Dropdown,
  Tabs,
  usePageMeta,
} from "frappe-ui";
import { computed, h, markRaw, onMounted, provide, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideGlobe from "~icons/lucide/globe";
import LucideMail from "~icons/lucide/mail";
import LucideMapPin from "~icons/lucide/map-pin";
import LucidePhone from "~icons/lucide/phone";
import LucideSquarePen from "~icons/lucide/square-pen";
import LucideSquareUser from "~icons/lucide/square-user";
import LucideTrash2 from "~icons/lucide/trash-2";
import { getTicketListResource } from "../../stores/docTickets";
// props with type set at string
const props = defineProps<{
  id: string;
}>();
const route = useRoute();
const router = useRouter();

const { isMobileView } = useScreenSize();
const { ticketsListResource, ticketsCountResource } = getTicketListResource();

const tabs = computed(() => [
  {
    label: __("Tickets"),
    hash: "tickets",
    count: ticketsCountResource.data ?? 0,
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
const { doc: customer, handleDelete } = useCustomer(props.id);
provide(CustomerResourceSymbol, customer);

const contactFilter = computed(() => {
  const contacts = customer.getContacts.data ?? [];
  if (contacts.length <= 1) return undefined;
  return {
    key: "contact",
    placeholder: __("Contact"),
    doctype: "Contact",
    filters: {
      name: [
        "in",
        contacts.map((c: { contact_name: string }) => c.contact_name),
      ],
    },
  };
});

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
const showDeleteDialog = ref(false);

const dropdownActions = computed(() => [
  {
    group: __("Danger"),
    hideLabel: true,
    items: [
      {
        label: __("Delete"),
        icon: LucideTrash2,
        theme: "red",
        onClick: () => {
          showDeleteDialog.value = true;
        },
      },
    ],
  },
]);

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
  if (hasPermission()) {
    customer.getPendingInvites.fetch();
  }
  customer.getContacts.fetch();
  ticketsListResource.update({
    filters: {
      customer: props.id,
    },
  });
  ticketsListResource.fetch();
  ticketsCountResource.fetch();
});

usePageMeta(() => {
  return {
    title: `Customer: ${props.id}`,
  };
});
</script>

<style scoped>
/* frappe-ui's TabsRoot clips with overflow-hidden, which traps the sticky
   tablist. Let it overflow so the tablist sticks to the page scroll container. */
.tabs-sticky-header {
  overflow: visible !important;
}
/* Same for the tab panels, so sticky children (e.g. the ticket filter bar)
   can stick to the page scroll container instead of being clipped. */
.tabs-sticky-header :deep([role="tabpanel"]) {
  overflow: visible !important;
}
.tabs-sticky-header :deep([role="tablist"]) {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: white;
}
</style>
