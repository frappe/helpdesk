<template>
  <div>
    <div class="flex items-center justify-between">
      <h1 class="text-lg font-semibold">Email Accounts</h1>
      <Button
        label="Add Account"
        theme="gray"
        variant="solid"
        @click="emit('update:step', 'email-add')"
      >
        <template #prefix>
          <LucidePlus class="h-4 w-4" />
        </template>
      </Button>
    </div>
    <div class="mt-4">
      <div v-for="emailAccount in emailAccounts.data" :key="emailAccount.name">
        <EmailAccountCard
          :emailAccount="emailAccount"
          @click="emit('update:step', 'email-edit', emailAccount)"
        />
      </div>
    </div>
  </div>
  <!-- <div
    class="flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl bg-gray-100 hover:bg-gray-200"
  >
    <img :src="emailIcon['GMail']" class="h-6 w-6" />
  </div> -->
</template>

<script setup lang="ts">
import { createListResource } from "frappe-ui";
import EmailAccountCard from "./EmailAccountCard.vue";
import { EmailAccountResource } from "@/types";

const emit = defineEmits(["update:step"]);

const emailAccounts = createListResource({
  doctype: "Email Account",
  cache: true,
  fields: [
    "name",
    "email_id",
    "service",
    "enable_incoming",
    "enable_outgoing",
    "api_key",
    "api_secret",
    "password",
  ],
  filters: {
    email_id: ["Not Like", "%example%"],
  },
  pageLength: 10,
  auto: true,
});
</script>

<style scoped></style>
