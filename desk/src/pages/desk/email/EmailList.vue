<template>
  <div class="flex flex-col">
    <PageTitle title="Email Accounts">
      <template #right>
        <RouterLink :to="{ name: AGENT_PORTAL_EMAIL_NEW }">
          <Button label="New email account" theme="gray" variant="solid">
            <template #prefix>
              <IconPlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </PageTitle>
    <ListView
      :columns="columns"
      :data="accounts.list?.data || []"
      :empty-message="emptyMessage"
      class="mt-2.5 grow"
      row-key="name"
    >
      <template #email_id="{ data }">
        <div class="flex justify-between">
          <span>{{ data.email_id }}</span>
          <div class="space-x-2">
            <Badge
              v-if="data.default_incoming"
              theme="blue"
              variant="subtle"
              size="md"
              >Default incoming</Badge
            >
            <Badge
              v-if="data.default_outgoing"
              theme="green"
              variant="subtle"
              size="md"
              >Default outgoing</Badge
            >
          </div>
        </div>
      </template>
      <template #enable_incoming="{ data }">
        <FormControl type="checkbox" :model-value="data.enable_incoming" />
      </template>
      <template #enable_outgoing="{ data }">
        <FormControl type="checkbox" :model-value="data.enable_outgoing" />
      </template>
    </ListView>
    <ListNavigation :resource="accounts" />
  </div>
</template>
<script setup lang="ts">
import { usePageMeta, Badge, FormControl } from "frappe-ui";
import { AGENT_PORTAL_EMAIL_NEW, AGENT_PORTAL_EMAIL_SINGLE } from "@/router";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import { ListView } from "@/components";
import ListNavigation from "@/components/ListNavigation.vue";
import IconPlus from "~icons/lucide/plus";

const emptyMessage = "No Email Accounts Found";
const columns = [
  {
    label: "Name",
    key: "name",
    width: "w-64",
  },
  {
    label: "Email",
    key: "email_id",
    width: "w-96",
  },
  {
    label: "Service",
    key: "service",
    width: "w-32",
  },
  {
    label: "Incoming",
    key: "enable_incoming",
    width: "w-20",
  },
  {
    label: "Outgoing",
    key: "enable_outgoing",
    width: "w-20",
  },
];

const accounts = createListManager({
  doctype: "Email Account",
  fields: [
    "name",
    "email_id",
    "service",
    "enable_incoming",
    "default_incoming",
    "enable_outgoing",
    "default_outgoing",
  ],
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = {
        name: AGENT_PORTAL_EMAIL_SINGLE,
        params: {
          emailAccountId: d.name,
        },
      };
    }
    return data;
  },
});

usePageMeta(() => {
  return {
    title: "Email accounts",
  };
});
</script>
