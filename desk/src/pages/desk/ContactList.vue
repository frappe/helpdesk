<template>
  <div class="flex flex-col">
    <PageTitle title="Contacts">
      <template #right>
        <Button
          icon-left="plus"
          label="New contact"
          class="bg-gray-900 text-white hover:bg-gray-800"
          @click="isDialogVisible = !isDialogVisible"
        />
      </template>
    </PageTitle>
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="contacts.list?.data || []"
      row-key="name"
      :emit-row-click="true"
      :hide-checkbox="true"
      :hide-column-selector="true"
      @row-click="goToContact"
    />
    <ListNavigation class="p-3" v-bind="contacts" />
    <NewContactDialog
      v-model="isDialogVisible"
      @contact-created="isDialogVisible = false"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { AGENT_PORTAL_CONTACT } from "@/router";
import { createListManager } from "@/composables/listManager";
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";

const router = useRouter();
const isDialogVisible = ref(false);
const columns = [
  {
    title: "Name",
    isTogglable: false,
    colKey: "name",
    colClass: "w-1/2",
  },
  {
    title: "Email",
    isTogglable: false,
    colKey: "email_id",
  },
];

const contacts = createListManager({
  doctype: "Contact",
  fields: ["name", "email_id"],
  auto: true,
});

function goToContact(id: string) {
  router.push({
    name: AGENT_PORTAL_CONTACT,
    params: {
      id,
    },
  });
}
</script>
