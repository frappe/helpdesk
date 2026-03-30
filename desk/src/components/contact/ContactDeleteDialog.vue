<template>
  <Dialog v-model="open" :options="{ title: __('Delete'), size: 'md' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              "Are you sure you want to delete this contact? This will permanently delete the contact from the system."
            )
          }}
        </p>
        <div class="flex flex-col gap-1">
          <p class="text-p-base text-ink-gray-7">
            {{
              __(
                `{0} ticket${
                  count === 1 ? "" : "s"
                } related to this contact and will also be deleted.`,
                [count]
              )
            }}
          </p>
        </div>
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
import { Button, createListResource, Dialog } from "frappe-ui";
import { computed, ref } from "vue";

const props = defineProps<{
  name: string;
}>();

const open = defineModel<boolean>("open", { default: false });

const resource = createListResource({
  doctype: "HD Ticket",
  filters: {
    contact: props.name,
  },
  fields: ["name"],
  auto: true,
});
const count = computed(() => {
  if (resource.loading) return 0;
  return resource.data?.length || 0;
});

const deleteLinkedTickets = ref(false);

const emit = defineEmits<{
  delete: [{ deleteLinkedTickets: boolean }];
}>();
</script>
