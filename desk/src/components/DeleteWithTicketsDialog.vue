<template>
  <Dialog v-model:open="open" :title="dialogTitle" size="md">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-7">{{ message }}</p>
        <Checkbox
          v-if="count"
          size="sm"
          v-model="deleteLinkedTickets"
          :label="__('Delete {0} ticket(s)', [count])"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          variant="solid"
          theme="red"
          icon-left="trash-2"
          :label="__('Delete')"
          :loading="isDeleting"
          @click="confirmDelete"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Button, Checkbox, createListResource, Dialog } from "frappe-ui";
import { computed, ref, watch } from "vue";

const props = defineProps<{
  /** Name of the record being deleted. */
  name: string;
  /** HD Ticket link field that ties tickets to this record. */
  linkField: "customer" | "contact";
  /** Confirmation copy shown above the checkbox. */
  message: string;
  title?: string;
  /** Async delete handler; the button stays in a loading state until it settles. */
  onDelete: (payload: { deleteLinkedTickets: boolean }) => Promise<void> | void;
}>();

const open = defineModel<boolean>({ default: false });

const resource = createListResource({
  doctype: "HD Ticket",
  filters: { [props.linkField]: props.name },
  fields: ["name"],
  limit: 99999, // We just want the count
});

const count = computed<number>(() => {
  if (resource.loading) return 0;
  return resource.data?.length ?? 0;
});

const deleteLinkedTickets = ref(false);
const isDeleting = ref(false);

const dialogTitle = computed(() => props.title ?? __("Delete"));

async function confirmDelete() {
  if (isDeleting.value) return;
  isDeleting.value = true;
  try {
    await props.onDelete({ deleteLinkedTickets: deleteLinkedTickets.value });
    open.value = false;
  } catch {
    // Keep the dialog open on failure; the handler surfaces the error.
  } finally {
    isDeleting.value = false;
  }
}

watch(
  open,
  (isOpen) => {
    if (isOpen) {
      resource.reload();
    }
  },
  { immediate: true }
);
</script>
