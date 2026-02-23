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
            <div v-if="tab.label === 'Tickets'">
              <!-- Tickets tab content -->
              {{ tab.label }}
              <CustomerTicketsTab />
            </div>
            <CustomerContactTab
              v-if="tab.label === 'Contacts'"
              :customer="id"
            />
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
import { CustomerResourceSymbol, DocumentResource } from "@/types";
import { HDCustomer } from "@/types/doctypes";
import {
  Breadcrumbs,
  createDocumentResource,
  Tabs,
  usePageMeta,
} from "frappe-ui";
import { computed, provide } from "vue";
import { useRoute, useRouter } from "vue-router";
import CustomerInfo from "./CustomerInfo.vue";
// props with type set at string
const props = defineProps<{
  id: string;
}>();

const route = useRoute();
const router = useRouter();

const tabs = [
  { label: "Tickets", hash: "tickets" },
  { label: "Contacts", hash: "contacts" },
];

const customer: DocumentResource<HDCustomer> = createDocumentResource({
  doctype: "HD Customer",
  name: props.id,
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
    label: "Customers",
    route: { name: "CustomerList" },
  },
  {
    label: props.id,
  },
];

usePageMeta(() => {
  return {
    title: props.id,
  };
});
</script>

<style scoped></style>
