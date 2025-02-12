<template>
  <Dialog
    v-model="show"
    :options="{
      title: 'Create View',
      actions: [
        {
          label: 'Create',
          variant: 'solid',
          onClick: emit('create'),
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-1.5 block text-base text-ink-gray-5">View Name</div>
      <div class="flex gap-2">
        <IconPicker v-model="view.icon" v-slot="{ togglePopover }">
          <Button
            size="md"
            class="flex size-8 text-2xl leading-none"
            :label="view.icon"
            @click="togglePopover"
          />
        </IconPicker>
        <FormControl
          class="flex-1"
          size="md"
          type="text"
          placeholder="My Open Tickets"
          v-model="view.label"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from "vue";
import { Dialog } from "frappe-ui";
import IconPicker from "@/components/IconPicker.vue";

const show = defineModel();

const view = ref({
  label: "",
  icon: "",
});

const emit = defineEmits(["create"]);
</script>
