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
          label: `${contact.doc.full_name}`.trim(),
          image: contact.doc.image ?? undefined,
          shape: 'circle',
        }"
        :doc-info="contactInfo"
        :badge="invitationName && __('Invited')"
      >
        <template #actions>
          <div class="flex gap-2 items-center">
            <Button
              variant="subtle"
              @click="showEditDialog = true"
              v-if="hasPermission()"
            >
              <div class="flex gap-1 items-center">
                <LucideSquarePen class="h-4 w-4" />
                <span>{{ __("Edit") }}</span>
              </div>
            </Button>
            <Dropdown
              :options="dropdownActions"
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
    <DeleteContactDialog
      v-model="showDeleteDialog"
      :name="id"
      @delete="handleDelete"
    />
    <EditContactDialog
      v-if="showEditDialog"
      v-model="showEditDialog"
      :name="id"
    />
  </div>
</template>

<script setup lang="ts">
import ContactFeedback from "@/components/contact/ContactFeedback.vue";
import DeleteContactDialog from "@/components/contact/DeleteContactDialog.vue";
import TicketsTab from "@/components/customer/TicketsTab.vue";
import TicketFeedbackIcon from "@/components/icons/TicketFeedbackIcon.vue";
import TicketHashIcon from "@/components/icons/TicketHashIcon.vue";
//@ts-ignore
import EditContactDialog from "@/components/contact/EditContactDialog.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import PageInfo from "@/components/PageInfo.vue";
import {
  useContact,
  useContactFeedback,
  useContactInvite,
  useContactResetPassword,
} from "@/composables/contact";
import { useScreenSize } from "@/composables/screen";
import { __ } from "@/translation";
import { hasPermission } from "@/utils";
import {
  Breadcrumbs,
  Button,
  call,
  Dropdown,
  Tabs,
  usePageMeta,
} from "frappe-ui";
import { computed, h, markRaw, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideMail from "~icons/lucide/mail";
import LucideMapPin from "~icons/lucide/map-pin";
import LucidePhone from "~icons/lucide/phone";
import LucideTrash2 from "~icons/lucide/trash-2";
import { getTicketListResource } from "../../stores/docTickets";

const props = defineProps<{
  id: string;
}>();

const route = useRoute();
const router = useRouter();
const { isMobileView } = useScreenSize();

const { doc: contact, state } = useContact(props.id);

const { feedbackCount } = useContactFeedback(props.id);

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
    count: feedbackCount.data ?? 0,
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

const { resendInvite, isLoading: isContactInvitationLoading } =
  useContactInvite();
const { resetPassword, isLoading: isResetPasswordLoading } =
  useContactResetPassword(() => contact.doc?.user);

const showEditDialog = ref(false);

const invitationName = computed(
  () => contact.getInfo.data?.invitation_name || ""
);

const showDeleteDialog = ref(false);
const dropdownActions = computed(() => {
  const baseActions = [];
  if (invitationName.value) {
    baseActions.push({
      label: __("Resend Invite"),
      icon: "mail",
      onClick: () => {
        resendInvite(invitationName.value);
      },
    });
  }
  if (contact.doc?.user) {
    baseActions.push({
      label: __("Send Reset Password Email"),
      icon: "mail",
      onClick: () => {
        resetPassword();
      },
    });
  }
  return [
    {
      group: __("Actions"),
      hideLabel: true,
      items: baseActions,
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
  ];
});
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
