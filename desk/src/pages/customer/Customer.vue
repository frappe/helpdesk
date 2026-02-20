<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="breadcrumbs"> </Breadcrumbs>
      </template>
    </LayoutHeader>
    <div class="gap-5 flex flex-col" v-if="!customer.loading && customer.doc">
      <!-- customer detail -->
      <div class="gap-x-3 flex p-5 pb-0">
        <!-- avatar -->
        <Avatar
          size="3xl"
          shape="square"
          :label="'Miro'"
          :image="customer.doc.image"
          class="h-[52px] w-[52px]"
        />
        <div class="flex flex-col h-full">
          <p class="font-medium text-ink-gray-8 text-xl mb-1.5">{{ id }}</p>
          <div class="flex items-center gap-x-1.5">
            <template v-for="(item, index) in customerInfo" :key="index">
              <template v-if="item.condition">
                <span
                  v-if="customerInfo.slice(0, index).some((i) => i.condition)"
                  class="text-ink-gray-4"
                  >•</span
                >
                <div class="flex items-center gap-x-1">
                  <component :is="item.icon" class="h-4 w-4 text-ink-gray-6" />
                  <span class="text-sm text-ink-gray-8">{{ item.value }}</span>
                </div>
              </template>
            </template>
          </div>
        </div>
      </div>
      <!-- Tabs -->
      <Tabs v-model="activeTab" :tabs="tabs">
        <template #tab-panel="{ tab }">
          <div class="p-5">
            <div v-show="tab.label === 'Tickets'">
              <!-- Tickets tab content -->
              {{ tab.label }}
            </div>
            <CustomerContactTab
              v-show="tab.label === 'Contacts'"
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
import LayoutHeader from "@/components/LayoutHeader.vue";
import { DocumentResource } from "@/types";
import { HDCustomer } from "@/types/doctypes";
import {
  Avatar,
  Breadcrumbs,
  createDocumentResource,
  Tabs,
  usePageMeta,
} from "frappe-ui";
import { computed, markRaw } from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideMail from "~icons/lucide/mail";
import LucidePhone from "~icons/lucide/phone";
import LucideSquareUser from "~icons/lucide/square-user";
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

const customerInfo = computed(() => {
  if (!customer.doc) return [];
  return [
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
      icon: markRaw(LucideSquareUser),
      value: `${customer.doc.contacts?.length ?? 0} ${
        customer.doc.contacts?.length === 1 ? "contact" : "contacts"
      }`,
      condition: true,
    },
  ];
});

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
    to: { name: "CustomerList" },
  },
  {
    label: props.id,
    to: { name: "Customer", params: { id: props.id } },
  },
];

usePageMeta(() => {
  return {
    title: props.id,
  };
});
</script>

<style scoped></style>
