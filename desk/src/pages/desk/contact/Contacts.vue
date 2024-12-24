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
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @row-click="openContact"
      @empty-state-action="isDialogVisible = true"
    />
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
import { computed, ref, h } from "vue";
import { usePageMeta, Avatar } from "frappe-ui";
import { ListViewBuilder, LayoutHeader } from "@/components";
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue";
import ContactDialog from "./ContactDialog.vue";
import { createToast } from "@/utils";
import { PhoneIcon } from "@/components/icons";

const isDialogVisible = ref(false);
const isContactDialogVisible = ref(false);
const selectedContact = ref(null);

const listViewRef = ref(null);
const options = computed(() => {
  return {
    doctype: "Contact",
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
  isDialogVisible.value = false;
  listViewRef.value?.reload();
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
  listViewRef.value?.reload();
}
usePageMeta(() => {
  return {
    title: "Contacts",
  };
});
</script>
