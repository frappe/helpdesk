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
      @row-click="openContact"
    >
      <template #name="{ data }">
        <div class="flex items-center gap-2">
          <Avatar :label="data.name" :image-u-r-l="data.image" size="sm" />
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

const isDialogVisible = ref(false);
const isContactDialogVisible = ref(false);
const selectedContact = ref(null);
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
