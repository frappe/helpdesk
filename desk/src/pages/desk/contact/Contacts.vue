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
          @click="showNewContactModal = !showNewContactModal"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @row-click="openContact"
      @empty-state-action="showNewContactModal = true"
    />
    <NewContactDialog
      v-model="showNewContactModal"
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
import { LayoutHeader, ListViewBuilder } from "@/components";
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue";
import { PhoneIcon } from "@/components/icons";
import { Avatar, toast, usePageMeta } from "frappe-ui";
import { computed, h, ref } from "vue";
import ContactDialog from "./ContactDialog.vue";
import { showNewContactModal } from "./dialogState";

const isContactDialogVisible = ref(false);
const selectedContact = ref(null);

const listViewRef = ref(null);
const options = computed(() => {
  return {
    doctype: "Contact",
    selectable: true,
    showSelectBanner: true,
    columnConfig: {
      full_name: {
        prefix: ({ row }) => {
          return h(Avatar, {
            shape: "circle",
            image: row.image,
            label: row.name,
            size: "sm",
          });
        },
      },
      mobile_no: {
        prefix: PhoneIcon,
      },
    },
    emptyState: {
      title: "No Contacts Found",
    },
  };
});

function handleContactCreated(): void {
  showNewContactModal.value = false;
  listViewRef.value?.reload();
}

function openContact(id: string): void {
  selectedContact.value = id;
  isContactDialogVisible.value = true;
}

function handleContactUpdated(): void {
  toast.success("Contact updated");
  isContactDialogVisible.value = !isContactDialogVisible.value;
  listViewRef.value?.reload();
}
usePageMeta(() => {
  return {
    title: "Contacts",
  };
});
</script>
