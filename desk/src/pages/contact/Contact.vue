<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="-ml-[2px]" />
      </template>
    </LayoutHeader>
    <div
      class="gap-5 flex flex-col h-full"
      v-if="!contact.loading && contact.doc"
    >
      <PageInfo
        :avatar="{
          label: `${contact.doc.first_name} ${
            contact.doc.last_name ?? ''
          }`.trim(),
          image: contact.doc.image ?? undefined,
          shape: 'circle',
        }"
        :doc-info="contactInfo"
        :showEdit="hasPermission()"
      />
      <Tabs v-model="activeTab" :tabs="tabs">
        <template #tab-item="{ tab, selected }: any">
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
            <TicketsTab
              v-if="tab.label === __('Tickets')"
              :doc="contact"
              :ticketsListResource="ticketsListResource"
              :baseFilter="{ contact: props.id }"
              :additionalFilter="
                (contact.getInfo.data?.customers?.length ?? 0) > 1
                  ? {
                      key: 'customer',
                      placeholder: __('Customer'),
                      doctype: 'HD Customer',
                      filters: {
                        name: ['in', contact.getInfo.data.customers.map((c: { name: string }) => c.name)],
                      },
                    }
                  : undefined
              "
            />
            <div v-if="tab.label === __('Feedback')">
              <!-- Feedback tab content -->
            </div>
          </div>
        </template>
      </Tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import TicketsTab from "@/components/customer/TicketsTab.vue";
import TicketFeedbackIcon from "@/components/icons/TicketFeedbackIcon.vue";
import TicketHashIcon from "@/components/icons/TicketHashIcon.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import PageInfo from "@/components/PageInfo.vue";
import { __ } from "@/translation";
import type { DocumentResource } from "@/types";
import type { Contact } from "@/types/doctypes";
import { hasPermission } from "@/utils";
import {
  Breadcrumbs,
  createDocumentResource,
  Tabs,
  usePageMeta,
} from "frappe-ui";
import { computed, h, markRaw, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideMail from "~icons/lucide/mail";
import LucideMapPin from "~icons/lucide/map-pin";
import LucidePhone from "~icons/lucide/phone";
import LucideStar from "~icons/lucide/star";
import { getTicketListResource } from "../customer/tickets";

const props = defineProps<{
  id: string;
}>();

const contact: DocumentResource<Contact> = createDocumentResource({
  doctype: "Contact",
  name: props.id,
  whitelistedMethods: {
    getInfo: "get_info",
  },
});

const route = useRoute();
const router = useRouter();

const { ticketsListResource } = getTicketListResource();

const tabs = computed(() => [
  {
    label: __("Tickets"),
    hash: "tickets",
    count: ticketsListResource.data?.length ?? 0,
    icon: h(TicketHashIcon, { class: "size-4" }),
  },
  {
    label: __("Feedback"),
    hash: "feedback",
    count: 0,
    icon: h(TicketFeedbackIcon, { class: "size-4" }),
  },
]);

const activeTab = computed<number>({
  get() {
    const index = tabs.value.findIndex((t) => t.hash === route.hash.slice(1));
    return index === -1 ? 0 : index;
  },
  set(i) {
    router.replace({ hash: i === 0 ? "" : `#${tabs.value[i].hash}` });
  },
});

const contactInfo = computed(() => {
  if (contact.getInfo.loading || !contact.getInfo.data || !contact.doc?.name) {
    return [];
  }
  const info = [
    {
      icon: h(LucideStar, {
        class: "size-4 !fill-ink-amber-2 !text-ink-amber-2",
      }),
      value: `${String(
        contact.getInfo?.data?.rating ?? 0
      )} Customers's Avg. Rating`,
      condition: !!contact.getInfo?.data?.rating,
    },
    {
      icon: markRaw(LucideMapPin),
      value: contact.getInfo?.data?.country,
      condition: !!contact.getInfo?.data?.country,
    },
    {
      icon: markRaw(LucideMail),
      value: contact.doc?.email_id,
      condition: !!contact.doc?.email_id,
    },
    {
      icon: markRaw(LucidePhone),
      value: contact.doc?.mobile_no,
      condition: !!contact.doc?.mobile_no,
    },
  ];
  return info;
});
const breadcrumbs = [
  {
    label: __("Contacts"),
    route: { name: "ContactList" },
  },
  {
    label: props.id,
  },
];

onMounted(() => {
  contact.getInfo.fetch();
  ticketsListResource.update({
    filters: {
      contact: props.id,
    },
  });
  ticketsListResource.fetch();
});

usePageMeta(() => {
  return {
    title: `Contact: ${props.id}`,
  };
});
</script>
