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
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="contacts.list?.data || []"
      row-key="name"
      :hide-checkbox="true"
      :hide-column-selector="true"
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
    </HelpdeskTable>
    <ListNavigation class="p-3" v-bind="contacts" />
    <AddNewAgentsDialog
      :show="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { Avatar, Badge } from "frappe-ui";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { createListManager } from "@/composables/listManager";
import { useListFilters } from "@/composables/listFilters";
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import IconPlus from "~icons/lucide/plus";

const router = useRouter();
const filters = useListFilters();
const isDialogVisible = ref(false);
const columns = [
  {
    title: "Name",
    colKey: "agent_name",
    colClass: "w-1/3",
  },
  {
    title: "Email",
    colKey: "user",
    colClass: "w-1/3",
  },
  {
    title: "Username",
    colKey: "user",
  },
];

const contacts = createListManager({
  doctype: "HD Agent",
  fields: ["*"],
  auto: true,
});

function toTickets(user: string) {
  const q = filters.toQuery([
    {
      fieldname: "_assign",
      filter_type: "is",
      value: user,
    },
  ]);

  router.push({
    name: AGENT_PORTAL_TICKET_LIST,
    query: {
      q,
    },
  });
}
</script>
