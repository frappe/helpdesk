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
      <!-- ContactInfo -->
      <PageInfo
        :avatar="{
          label: `${contact.doc.first_name} ${
            contact.doc.last_name ?? ''
          }`.trim(),
          image: contact.doc.image ?? undefined,
          shape: 'circle',
        }"
        :doc-info="contactInfo"
      >
        <template #actions>
          <div class="flex gap-2 items-center">
            <Button variant="subtle">
              <div class="flex gap-1 items-center">
                <LucideSquarePen class="h-4 w-4" />
                <span>{{ __("Edit") }}</span>
              </div>
            </Button>
            <Dropdown
              :options="moreOptions"
              placement="right"
              v-if="hasPermission()"
            >
              <Button icon="more-horizontal" variant="subtle" />
            </Dropdown>
          </div>
        </template>
      </PageInfo>
      <div class="overflow-y-auto flex-1">
        <TicketStats :dt="'Contact'" :dn="id" v-if="!isMobileView" />
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
                <ContactFeedback :name="props.id" />
              </div>
            </div>
          </template>
        </Tabs>
      </div>
    </div>
  </div>
  <ContactDeleteDialog
    v-model:open="showDeleteDialog"
    :name="id"
    @delete="handleDelete"
  />
</template>

<script setup lang="ts">
import ContactDeleteDialog from "@/components/contact/ContactDeleteDialog.vue";
import ContactFeedback from "@/components/contact/ContactFeedback.vue";
import TicketsTab from "@/components/customer/TicketsTab.vue";
import TicketFeedbackIcon from "@/components/icons/TicketFeedbackIcon.vue";
import TicketHashIcon from "@/components/icons/TicketHashIcon.vue";
//@ts-ignore
import LayoutHeader from "@/components/LayoutHeader.vue";
import PageInfo from "@/components/PageInfo.vue";
import {
  useContactInvite,
  useContactResetPassword,
} from "@/composables/contact";
import { useScreenSize } from "@/composables/screen";
import { __ } from "@/translation";
import type { DocumentResource } from "@/types";
import type { Contact } from "@/types/doctypes";
import { hasPermission } from "@/utils";
import {
  Breadcrumbs,
  Button,
  call,
  createDocumentResource,
  Dropdown,
  Tabs,
  usePageMeta,
} from "frappe-ui";
import { computed, h, markRaw, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideMail from "~icons/lucide/mail";
import LucideMapPin from "~icons/lucide/map-pin";
import LucidePhone from "~icons/lucide/phone";
import LucideStar from "~icons/lucide/star";
import LucideTrash2 from "~icons/lucide/trash-2";
import { getTicketListResource } from "../../stores/docTickets";

const props = defineProps<{
  id: string;
}>();

const route = useRoute();
const router = useRouter();
const { isMobileView } = useScreenSize();

const contact: DocumentResource<Contact> = createDocumentResource({
  doctype: "Contact",
  name: props.id,
  whitelistedMethods: {
    getInfo: "get_info",
  },
});

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

const { inviteContact, isLoading: isContactInvitationLoading } =
  useContactInvite(contact);
const { resetPassword, isLoading: isResetPasswordLoading } =
  useContactResetPassword(() => contact.doc?.user);

const showDeleteDialog = ref(false);
const moreOptions = computed(() => [
  {
    group: __("Actions"),
    hideLabel: true,
    items: [
      {
        label: __("Invite as User"),
        icon: "user-plus",
        condition: () => !contact.doc?.user,
        onClick: () => {
          inviteContact();
        },
      },
      {
        label: __("Send Reset Password Email"),
        icon: "mail",
        onClick: () => {
          resetPassword();
        },
      },
    ],
  },
  {
    group: __("Danger"),
    hideLabel: true,
    items: [
      {
        label: __("Delete"),
        icon: LucideTrash2,
        theme: "red",
        onClick: () => {
          // TODO: delete contact
          showDeleteDialog.value = true;
        },
      },
    ],
  },
]);
function handleDelete({
  deleteLinkedTickets,
}: {
  deleteLinkedTickets: boolean;
}) {
  call("helpdesk.api.contact.delete_contact", {
    name: props.id,
    delete_linked_tickets: deleteLinkedTickets,
  }).then(() => {
    router.push({ name: "ContactList" });
  });
}

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
