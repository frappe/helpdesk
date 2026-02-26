<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="breadcrumbs"> </Breadcrumbs>
      </template>
    </LayoutHeader>
    <div class="gap-5 flex flex-col" v-if="!customer.loading && customer.doc">
      <!-- customer detail -->
      <CustomerInfo />
      <!-- Tabs -->
      <Tabs v-model="activeTab" :tabs="tabs">
        <template #tab-panel="{ tab }">
          <div class="p-5">
            <div v-if="tab.label === __('Tickets')">
              <!-- Tickets tab content -->
              {{ tab.label }}
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
import LayoutHeader from "@/components/LayoutHeader.vue";
import { __ } from "@/translation";
import { CustomerResourceSymbol, DocumentResource } from "@/types";
import { HDCustomer } from "@/types/doctypes";
import {
  Breadcrumbs,
  createDocumentResource,
  Tabs,
  usePageMeta,
} from "frappe-ui";
import { computed, onMounted, provide } from "vue";
import { useRoute, useRouter } from "vue-router";
import CustomerInfo from "./CustomerInfo.vue";
// props with type set at string
const props = defineProps<{
  id: string;
}>();

const route = useRoute();
const router = useRouter();

const tabs = [
  { label: __("Tickets"), hash: "tickets" },
  { label: __("Contacts"), hash: "contacts" },
];
const customer: DocumentResource<HDCustomer> = createDocumentResource({
  doctype: "HD Customer",
  name: props.id,
  whitelistedMethods: {
    updateContacts: "update_contacts",
    getPendingInvites: "get_pending_invites",
    getContacts: "get_contacts",
  },
});

provide(CustomerResourceSymbol, customer);

const activeTab = computed<number>({
  get() {
    const index = tabs.findIndex((t) => t.hash === route.hash.slice(1));
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
    router.replace({ hash: `#${tabs[i].hash}` });
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
});

usePageMeta(() => {
  return {
    title: props.id,
  };
});
</script>
