<template>
  <div class="flex flex-col">
    <PageTitle title="Agents">
      <template #right>
        <Button
          label="New agent"
          theme="gray"
          variant="solid"
          @click="isDialogVisible = !isDialogVisible"
        >
          <template #prefix>
            <IconPlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
    <ListView
      :columns="columns"
      :data="agents.list?.data"
      :empty-message="emptyMessage"
      class="mt-2.5 grow"
      row-key="name"
    >
      <template #name="{ data }">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Avatar :label="data.name" :image="data.user_image" size="sm" />
            <div class="line-clamp-1">{{ data.full_name }}</div>
          </div>
          <Badge
            v-if="!data.is_active"
            size="md"
            theme="orange"
            variant="subtle"
            >Inactive</Badge
          >
        </div>
      </template>
      <template #row-extra="{ data }">
        <div class="cursor-pointer text-xs" @click="toTickets(data.name)">
          Tickets &rightarrow;
        </div>
      </template>
    </ListView>
    <ListNavigation :resource="agents" />
    <AddNewAgentsDialog
      :show="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { usePageMeta, Avatar, Badge } from "frappe-ui";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { createListManager } from "@/composables/listManager";
import { useFilter } from "@/composables/filter";
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import { ListView } from "@/components";
import ListNavigation from "@/components/ListNavigation.vue";
import IconPlus from "~icons/lucide/plus";

const { apply, storage } = useFilter("HD Ticket");
const isDialogVisible = ref(false);
const emptyMessage = "No Agents Found";
const columns = [
  {
    label: "Name",
    key: "name",
    width: "w-80",
  },
  {
    label: "Email",
    key: "email",
    width: "w-80",
  },
  {
    label: "Username",
    key: "username",
    width: "w-80",
  },
];

const agents = createListManager({
  doctype: "HD Agent",
  fields: [
    "name",
    "is_active",
    "user.full_name",
    "user.user_image",
    "user.email",
    "user.username",
  ],
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = () => toTickets(d.name);
    }
    return data;
  },
});

usePageMeta(() => {
  return {
    title: "Agents",
  };
});

function toTickets(user: string) {
  storage.value.clear();
  storage.value.add({
    fieldname: "_assign",
    operator: "is",
    value: user,
  });
  apply({
    name: AGENT_PORTAL_TICKET_LIST,
  });
}
</script>
