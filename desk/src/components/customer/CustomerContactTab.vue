<template>
  <div>
    <div class="flex items-center justify-between">
      <p class="mt-2.5 mb-4.5 font-semibold text-lg">{{ __("Contacts") }}</p>
      <Dropdown :options="headerOptions" placement="right">
        <Button :label="__('New')" variant="subtle" v-if="hasPermission()">
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </Dropdown>
    </div>
    <!-- Loading -->
    <div v-if="contacts.loading" class="flex justify-center py-10">
      <LoadingIndicator :scale="10" />
    </div>
    <!-- Empty state -->
    <div
      v-else-if="!contacts.data?.length"
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
    <div v-else class="flex flex-wrap gap-4">
      <ContactCard
        v-for="contact in contacts.data"
        :key="contact.contact_name"
        :contact="contact"
        @update="contacts.reload()"
      />
    </div>
  </div>
  <AddExistingUserModal
    v-model="showAddContact"
    :existing-users="existingContacts"
    @invited="handleContactInvite"
    :for-agents="false"
  />
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { CustomerContact, CustomerResourceSymbol, Resource } from "@/types";
import { hasPermission } from "@/utils";
import { createResource, Dropdown, LoadingIndicator, toast } from "frappe-ui";
import { computed, inject, onMounted, ref } from "vue";
import LucideUserX from "~icons/lucide/user-x";
import AddExistingUserModal from "../AddExistingUserModal.vue";
import { agents } from "../Settings/agents";
import ContactCard from "./ContactCard.vue";

const customer = inject(CustomerResourceSymbol)!;

const showAddContact = ref(false);

const contacts: Resource<CustomerContact[]> = createResource({
  url: "helpdesk.helpdesk.doctype.hd_customer.hd_customer.get_contacts_for_customer",
  params: { customer: customer.doc.name },
  cache: ["CustomerContact", customer.doc.name],
  auto: true,
  transform: (data: CustomerContact[]) => {
    return data.sort((a, b) => {
      if (a.is_primary) return -1;
      if (b.is_primary) return 1;
      return 0;
    });
  },
});

const existingContacts = computed(() => {
  if (agents.loading && contacts.loading) return [];
  if (!agents.data && !contacts.data) return [];

  return [
    ...new Set([
      ...(agents.data?.map((a) => a.user) || []),
      ...(contacts.data?.map((c) => c.email_id) || []),
      "Guest",
    ]),
  ];
});
function reload() {
  contacts.reload();
  customer.reload();
}

function handleContactInvite(data: { users: string[]; role: string }) {
  customer.updateContacts.submit(
    {
      contacts: JSON.stringify(data.users),
      role: data.role,
    },
    {
      onSuccess: () => {
        showAddContact.value = false;
        reload();
        toast.success(__("Contacts added successfully"));
      },
    }
  );
}

const headerOptions = [
  {
    label: __("Add existing contact"),
    onClick: () => {
      showAddContact.value = true;
    },
  },
  {
    label: __("Invite new contact"),
    onClick: () => {},
  },
];

onMounted(() => {
  agents.fetch();
});
</script>
