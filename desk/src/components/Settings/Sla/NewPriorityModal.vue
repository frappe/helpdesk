<template>
  <Dialog v-model="dialog.show">
    <template #body-title>
      <h3 class="text-2xl font-semibold">New row</h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :type="'select'"
          size="sm"
          variant="subtle"
          placeholder="Select Priority"
          label="Priority"
          v-model="priorityData.priority"
          :options="[
            {
              label: 'Low',
              value: 'Low',
            },
            {
              label: 'Medium',
              value: 'Medium',
            },
            {
              label: 'High',
              value: 'High',
            },
          ]"
          required
        />
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Resolution Time"
          label="Resolution Time"
          v-model="priorityData.resolution_time"
          required
        />
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Response Time"
          label="Response Time"
          v-model="priorityData.response_time"
          required
        />
        <Checkbox
          v-model="priorityData.default_priority"
          label="Set default priority"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between">
        <div>
          <Button variant="subtle" theme="red" label="Delete">
            <template #prefix>
              <FeatherIcon name="trash-2" class="size-4" />
            </template>
          </Button>
        </div>
        <div class="flex gap-2">
          <Button variant="subtle" theme="gray" @click="dialog.show = false">
            Cancel
          </Button>
          <Button variant="solid" @click="onSave"> Save </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Dialog, FormControl, Checkbox } from "frappe-ui";

const dialog = defineModel<{
  show: boolean;
  onSave: (data: any) => void;
}>();

const priorityData = ref({
  priority: "",
  resolution_time: "",
  response_time: "",
  default_priority: false,
});

function onSave() {
  // createResource({
  //   url: "frappe.client.insert",
  //   params: {
  //     doc: {
  //       doctype: "HD Service Level Priority",
  //       priority: priorityData.value.priority,
  //       resolution_time: priorityData.value.resolution_time,
  //       response_time: priorityData.value.response_time,
  //       default_priority: priorityData.value.default_priority,
  //       parent: props.parent,
  //       parenttype: "HD Service Level Agreement",
  //       parentfield: "priorities",
  //     },
  //   },
  //   auto: true,
  //   onSuccess: () => {
  //     dialog.value = false;
  //   },
  // });
}
</script>
