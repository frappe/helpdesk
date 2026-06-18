<template>
  <Dialog v-model:open="open" :title="__('Delete')" size="md">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              "Are you sure you want to delete this contact? The contact will be permanently deleted and unlinked from any associated customers."
            )
          }}
        </p>
        <Checkbox
          v-if="count"
          size="sm"
          v-model="deleteLinkedTickets"
          :label="__('Delete {0} linked ticket(s)', [count])"
        />
      </div>
    </template>
    <template #actions="{ close }">
      <div class="flex gap-2 w-full">
        <Button
          variant="solid"
          theme="red"
          class="w-full"
          icon-left="trash-2"
          @click="
            () => {
              emit('delete', { deleteLinkedTickets });
              close();
            }
          "
        >
          {{ __("Delete") }}
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Button, Checkbox, createListResource, Dialog } from "frappe-ui";
import { computed, ref } from "vue";

const props = defineProps<{
  name: string;
}>();

const open = defineModel<boolean>({ default: false });

const resource = createListResource({
  doctype: "HD Ticket",
  filters: {
    contact: props.name,
  },
  fields: ["name"],
  auto: true,
});
const count = computed<number>(() => {
  if (resource.loading) return 0;
  return resource.data?.length ?? 0;
});

const deleteLinkedTickets = ref(false);

const emit = defineEmits<{
  delete: [{ deleteLinkedTickets: boolean }];
}>();
</script>
