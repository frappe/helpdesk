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
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
    <ListView
      :columns="columns"
      :resource="contacts"
      class="mt-2.5"
      doctype="Contact"
    >
      <template #name="{ data }">
        <div class="flex items-center gap-2">
          <Avatar :label="data.name" :image="data.image" size="sm" />
          <div class="line-clamp-1">{{ data.name }}</div>
        </div>
      </template>
    </ListView>
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
import { usePageMeta, Avatar } from "frappe-ui";
import { createListManager } from "@/composables/listManager";
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import { ListView } from "@/components";
import ContactDialog from "./ContactDialog.vue";

const isDialogVisible = ref(false);
const isContactDialogVisible = ref(false);
const selectedContact = ref(null);
const columns = [
  {
    label: "Name",
    key: "name",
    width: "w-80",
  },
  {
    label: "Email",
    key: "email_id",
    width: "w-80",
  },
  {
    label: "Phone",
    key: "phone",
    width: "w-80",
  },
];

const contacts = createListManager({
  doctype: "Contact",
  fields: ["name", "email_id", "image", "phone"],
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = () => openContact(d.name);
    }
    return data;
  },
});

usePageMeta(() => {
  return {
    title: "Contacts",
  };
});

function openContact(id: string) {
  selectedContact.value = id;
  isContactDialogVisible.value = true;
}
</script>
