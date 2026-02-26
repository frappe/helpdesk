<template>
  <div>
    <div class="flex items-center justify-between">
      <p class="mt-2.5 mb-4.5 font-semibold text-lg">{{ __("Contacts") }}</p>
      <div class="flex items-center gap-1">
        <Button
          :label="pendingInvitesLabel"
          v-if="pendingInvitesLabel"
          variant="ghost"
          @click="showPendingInvites = true"
        />
        <Dropdown :options="headerOptions" placement="right">
          <Button :label="__('New')" variant="subtle" v-if="hasPermission()">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </Dropdown>
      </div>
    </div>
    <!-- Loading -->
    <div v-if="customer.getContacts?.loading" class="flex justify-center py-10">
      <LoadingIndicator :scale="10" />
    </div>
    <!-- Empty state -->
    <div
      v-else-if="!customer.getContacts?.data?.length"
      class="flex flex-col items-center justify-center gap-3 py-16 text-center"
    >
      <LucideUserX class="h-10 w-10 text-ink-gray-4" />
      <div>
        <!-- make font larger -->
        <p class="text-lg font-medium text-ink-gray-7">
          {{ __("No contacts found") }}
        </p>
      </div>
    </div>
    <!-- Contacts list -->
    <div v-else class="grid grid-cols-3 gap-4">
      <ContactCard
        v-for="contact in customer.getContacts?.data"
        :key="contact.contact_name"
        :contact="contact"
        @update="customer.getContacts?.reload()"
      />
    </div>
  </div>
  <AddUserModal
    v-model="showAddContact"
    :existing-users="existingContacts"
    :for-agents="false"
    :invite-new="inviteNewUsers"
    @addedExisting="handleAddExistingContacts"
    @invited="handleInviteContacts"
  />
  <PendingInvitesModal
    v-if="Boolean(customer.getPendingInvites?.data?.length)"
    v-model="showPendingInvites"
    :pending-invites="customer.getPendingInvites?.data || []"
    @invites-updated="customer.getPendingInvites?.fetch()"
  />
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import { hasPermission } from "@/utils";
import {
  Button,
  createResource,
  Dropdown,
  LoadingIndicator,
  toast,
} from "frappe-ui";
import { computed, inject, onMounted, ref } from "vue";
import LucideUserX from "~icons/lucide/user-x";
import AddUserModal from "../AddUserModal.vue";
import { agents } from "../Settings/agents";
import ContactCard from "./ContactCard.vue";
import PendingInvitesModal from "./PendingInvitesModal.vue";

const customer = inject(CustomerResourceSymbol)!;

const showAddContact = ref(false);
const inviteNewUsers = ref(false);

const existingContacts = computed(() => {
  if (agents.loading && customer.getContacts?.loading) return [];
  if (!agents.data && !customer.getContacts?.data) return [];

  return [
    ...new Set([
      ...(agents.data?.map((a) => a.user) || []),
      ...(customer.getContacts?.data?.map((c) => c.email_id) || []),
      "Guest",
    ]),
  ];
});
function reload(onlyContacts = false) {
  customer.reload();
  if (onlyContacts) {
    customer.getContacts.reload();
    return;
  }
  customer.getPendingInvites.reload();
}

function handleAddExistingContacts(data: { contacts: string[]; role: string }) {
  customer.updateContacts.submit(
    {
      contacts: JSON.stringify(data.contacts),
      role: data.role,
    },
    {
      onSuccess: () => {
        showAddContact.value = false;
        reload(true);
        toast.success(__("Contacts added successfully"));
      },
    }
  );
}

const inviteByEmailResource = createResource({
  url: "frappe.core.api.user_invitation.invite_by_email",
});

function handleInviteContacts(data: { contacts: string; role: string }) {
  inviteByEmailResource.submit(
    {
      emails: data.contacts,
      roles: [data.role],
      redirect_to_path: "/helpdesk",
      app_name: "helpdesk",
      custom_customer: customer.doc?.name,
    },
    {
      onSuccess() {
        showAddContact.value = false;
        reload(false);
        toast.success(__("Contacts invited successfully"));
      },
    }
  );
}

const pendingInvitesLabel = computed(() => {
  if (customer.getPendingInvites.loading) return null;
  if (!customer.getPendingInvites.data) return null;
  const pendingInvites = customer.getPendingInvites.data;
  if (pendingInvites.length === 0) return null;
  return pendingInvites.length === 1
    ? __("1 pending invite")
    : __("{0} pending invites", [pendingInvites.length]);
});

const headerOptions = [
  {
    label: __("Add existing contact"),
    onClick: () => {
      inviteNewUsers.value = false;
      showAddContact.value = true;
    },
  },
  {
    label: __("Invite new contact"),
    onClick: () => {
      inviteNewUsers.value = true;
      showAddContact.value = true;
    },
  },
];

const showPendingInvites = ref(false);

onMounted(() => {
  agents.fetch();
});
</script>
