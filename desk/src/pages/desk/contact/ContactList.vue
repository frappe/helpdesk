<template>
  <div class="flex flex-col">
    <PageTitle title="Contacts">
      <template #right>
        <Button
          label="New contact"
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
      :columns="columns"
      :data="contacts.list?.data || []"
      :emit-row-click="true"
      :empty-message="emptyMessage"
      :hide-checkbox="true"
      :hide-column-selector="true"
      :row-click="{
        type: 'action',
        fn: openContact,
      }"
      class="grow"
      row-key="name"
    >
      <template #name="{ data }">
        <div class="flex items-center gap-2">
          <Avatar :label="data.name" :image="data.image" size="sm" />
          <div class="line-clamp-1">{{ data.name }}</div>
        </div>
      </template>
    </HelpdeskTable>
    <ListNavigation class="p-3" v-bind="contacts" />
    <NewContactDialog
      v-model="isDialogVisible"
      @contact-created="isDialogVisible = false"
    />
    <span v-if="isContactDialogVisible">
      <ContactDialog v-model="isContactDialogVisible" :name="selectedContact" />
    </span>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { Avatar } from "frappe-ui";
import { createListManager } from "@/composables/listManager";
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import ContactDialog from "./ContactDialog.vue";
import IconPlus from "~icons/lucide/plus";

const isDialogVisible = ref(false);
const isContactDialogVisible = ref(false);
const selectedContact = ref(null);
const emptyMessage = "No Contacts Found";
const columns = [
  {
    title: "Name",
    colKey: "name",
    colClass: "w-1/3",
  },
  {
    title: "Email",
    colKey: "email_id",
    colClass: "w-1/3",
  },
  {
    title: "Phone",
    colKey: "phone",
  },
];

const contacts = createListManager({
  doctype: "Contact",
  fields: ["name", "email_id", "image", "phone"],
  auto: true,
});

function openContact(id: string) {
  selectedContact.value = id;
  isContactDialogVisible.value = true;
}
</script>
