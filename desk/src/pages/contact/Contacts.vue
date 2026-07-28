<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">
          {{ __("Contacts") }}
        </div>
      </template>
      <template #right-header>
        <Button
          :label="__('Create')"
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
    <ListViewBuilder ref="listViewRef" :options="options" />
    <NewContactDialog v-model="showNewContactModal" />
  </div>
</template>
<script setup lang="ts">
import { LayoutHeader, ListViewBuilder } from "@/components";
import NewContactDialog from "@/components/contact/NewContactDialog.vue";
import { PhoneIcon } from "@/components/icons";
import { __ } from "@/translation";
import { Avatar, usePageMeta } from "frappe-ui";
import { computed, h, ref } from "vue";
import LucideContact2 from "~icons/lucide/contact-2";
import { showNewContactModal } from "./dialogState";

const hasActiveFilters = computed(
  () => Object.keys(listViewRef.value?.list?.params?.filters || {}).length > 0
);
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
        prefix: ({ row }) => (row.mobile_no ? h(PhoneIcon) : null),
      },
    },
    emptyState: {
      title: "No contacts found",
      icon: h(LucideContact2, {
        class: "h-10 w-10",
      }),
      description: hasActiveFilters.value
        ? __(
            "No contacts found for the applied filters. Try adjusting or clearing your filters."
          )
        : undefined,
    },
    rowRoute: {
      name: "Contact",
      prop: "id",
    },
  };
});

usePageMeta(() => {
  return {
    title: "Contacts",
  };
});
</script>
