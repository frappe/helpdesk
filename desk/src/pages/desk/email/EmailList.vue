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
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="accounts.list?.data || []"
      row-key="name"
      :emit-row-click="true"
      :hide-checkbox="true"
      :hide-column-selector="true"
      @row-click="gotoAccount"
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
        <Input type="checkbox" :disabled="true" :value="data.enable_incoming" />
      </template>
      <template #enable_outgoing="{ data }">
        <Input type="checkbox" :disabled="true" :value="data.enable_outgoing" />
      </template>
    </HelpdeskTable>
    <ListNavigation class="p-3" v-bind="accounts" />
  </div>
</template>
<script setup lang="ts">
import { useRouter } from "vue-router";
import { Badge, Input } from "frappe-ui";
import { AGENT_PORTAL_EMAIL_NEW, AGENT_PORTAL_EMAIL_SINGLE } from "@/router";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import IconPlus from "~icons/lucide/plus";

const router = useRouter();
const columns = [
  {
    title: "Name",
    colKey: "name",
    colClass: "w-1/4",
  },
  {
    title: "Email",
    colKey: "email_id",
    colClass: "grow",
  },
  {
    title: "Service",
    colKey: "service",
    colClass: "w-32",
  },
  {
    title: "Incoming",
    colKey: "enable_incoming",
    colClass: "w-20",
  },
  {
    title: "Outgoing",
    colKey: "enable_outgoing",
    colClass: "w-20",
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
});

function gotoAccount(id: string) {
  router.push({
    name: AGENT_PORTAL_EMAIL_SINGLE,
    params: {
      emailAccountId: id,
    },
  });
}
</script>
