<template>
  <div>
    <div class="flex items-center justify-between">
      <p class="mt-2.5 mb-4.5 font-semibold text-lg">Contacts</p>
      <Dropdown :options="headerOptions" placement="right">
        <Button :label="__('Create')" variant="solid">
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
        <p class="text-lg font-medium text-ink-gray-7">No contacts found</p>
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
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { CustomerContact, Resource } from "@/types";
import { createResource, Dropdown, LoadingIndicator } from "frappe-ui";
import LucideUserX from "~icons/lucide/user-x";
import ContactCard from "./ContactCard.vue";

const props = defineProps<{
  customer: string;
}>();

const contacts = createResource<Resource<CustomerContact[]>>({
  url: "helpdesk.helpdesk.doctype.hd_customer.hd_customer.get_contacts_for_customer",
  params: { customer: props.customer },
  cache: ["CustomerContact", props.customer],
  auto: true,
  transform: (data: CustomerContact[]) => {
    return data.sort((a, b) => {
      if (a.is_primary) return -1;
      if (b.is_primary) return 1;
      return 0;
    });
  },
});
const headerOptions = [
  {
    label: __("Add existing contact"),
    onClick: () => {},
  },
  {
    label: __("Invite new contact"),
    onClick: () => {},
  },
];
</script>

<style scoped></style>
