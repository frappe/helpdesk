<template>
  <div>
    <div class="flex items-center justify-between pb-4">
      <p class="text-md-semibold">{{ __("Contacts") }}</p>
      <Button
        v-if="hasPermission()"
        :label="__('Invite')"
        variant="subtle"
        @click="showInviteContact = true"
      >
        <template #prefix>
          <LucidePlus class="h-4 w-4" />
        </template>
      </Button>
    </div>
    <!-- Loading -->
    <div v-if="customer.getContacts?.loading" class="flex justify-center py-10">
      <LoadingIndicator :scale="10" />
    </div>
    <!-- Empty state -->
    <div
      v-else-if="!customer.getContacts?.data?.length"
      class="flex flex-col items-center justify-center gap-3 py-16 text-center h-full flex-1"
    >
      <LucideUserX class="size-7.5 text-ink-gray-4" />
      <div>
        <!-- make font larger -->
        <p class="text-md-medium text-ink-gray-7">
          {{ __("No contacts found") }}
        </p>
      </div>
    </div>
    <!-- Contacts list -->
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <ContactCard
        v-for="contact in customer.getContacts?.data"
        :key="contact.contact_name"
        :contact="contact"
        @update="customer.getContacts?.reload()"
      />
    </div>
  </div>
  <InviteContactDialog
    v-model="showInviteContact"
    :excluded-emails="existingContacts"
  />
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import { hasPermission } from "@/utils";
import { Button, LoadingIndicator } from "frappe-ui";
import { computed, inject, onMounted, ref } from "vue";
import LucidePlus from "~icons/lucide/plus";
import LucideUserX from "~icons/lucide/user-x";
import { agents } from "../Settings/agents";
import ContactCard from "./ContactCard.vue";
import InviteContactDialog from "./InviteContactDialog.vue";

const customer = inject(CustomerResourceSymbol)!;

const showInviteContact = ref(false);

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

onMounted(() => {
  agents.fetch();
});
</script>
