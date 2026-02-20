<template>
  <div>
    <p class="mt-2.5 mb-4.5 font-semibold text-lg">Contacts</p>
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
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { CustomerContact, Resource } from "@/types";
import { createResource, LoadingIndicator } from "frappe-ui";
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
  //   transform the response and say whicher is primar will be first
  transform: (data: CustomerContact[]) => {
    return data.sort((a, b) => {
      if (a.is_primary) return -1;
      if (b.is_primary) return 1;
      return 0;
    });
  },
});
</script>

<style scoped></style>
