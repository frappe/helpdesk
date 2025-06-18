<template>
  <div class="flex items-center py-2">
    <div class="w-4/5">
      <div class="text-base">{{ data.name }}</div>
      <div
        class="text-sm w-11/12 text-gray-500 mt-1 whitespace-nowrap overflow-ellipsis overflow-hidden"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="flex justify-between items-center w-1/5">
      <div>
        <Switch
          size="sm"
          :modelValue="data.enabled"
          @update:modelValue="onToggle"
        />
      </div>
      <div>
        <Dropdown
          :options="[
            {
              label: 'Edit',
              onClick: () => editSla(),
              icon: 'edit',
            },
            {
              label: 'Duplicate',
              onClick: () => duplicate(),
              icon: 'copy',
            },
            {
              label: isConfirmingDelete ? 'Confirm Delete' : 'Delete',
              onClick: () => deleteSla(),
              icon: 'trash-2',
            },
          ]"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { Switch, Button, Dropdown, createResource } from "frappe-ui";
import { ref } from "vue";
import { activeScreen, slaPolicyListData } from "./sla";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const isConfirmingDelete = ref(false);

const duplicate = () => {
  createResource({
    url: "helpdesk.api.sla.duplicate_sla",
    params: {
      docname: props.data.name,
    },
    onSuccess: () => {
      slaPolicyListData.reload();
    },
    auto: true,
  });
};

const editSla = () => {
  activeScreen.value = {
    screen: "view",
    data: props.data,
  };
};

const deleteSla = () => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    setTimeout(() => {
      isConfirmingDelete.value = false;
    }, 3000);
    return;
  }

  createResource({
    url: "frappe.client.delete",
    params: {
      doctype: "HD Service Level Agreement",
      name: props.data.name,
    },
    onSuccess: () => {
      slaPolicyListData.reload();
      isConfirmingDelete.value = false;
    },
    auto: true,
  });
};

const onToggle = () => {
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "HD Service Level Agreement",
      name: props.data.name,
      fieldname: "enabled",
      value: !props.data.enabled,
    },
    onSuccess: () => {
      slaPolicyListData.reload();
    },
    auto: true,
  });
};
</script>
