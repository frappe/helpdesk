<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Contacts</div>
      </template>
      <template #right-header>
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
    </LayoutHeader>
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
      @contact-created="handleContactCreated"
    />
    <ContactDialog
      v-if="isContactDialogVisible"
      :key="selectedContact"
      v-model="isContactDialogVisible"
      :name="selectedContact"
      @contact-updated="handleContactUpdated"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { usePageMeta, Avatar } from "frappe-ui";
import { createListManager } from "@/composables/listManager";
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { ListView } from "@/components";
import ContactDialog from "./ContactDialog.vue";
import { createToast } from "@/utils";
import { Column } from "@/types";

const isDialogVisible = ref(false);
const isContactDialogVisible = ref(false);
const selectedContact = ref(null);

const columns: Column[] = [
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

function handleContactCreated(): void {
  isDialogVisible.value = false;
  contacts.reload();
}

function openContact(id: string): void {
  selectedContact.value = id;
  isContactDialogVisible.value = true;
}

function handleContactUpdated(): void {
  createToast({
    title: "Contact updated",
    icon: "check",
    iconClasses: "text-green-500",
  });
  isContactDialogVisible.value = !isContactDialogVisible.value;
  contacts.reload();
}
</script>
