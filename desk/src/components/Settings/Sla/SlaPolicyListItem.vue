<template>
  <div
    class="grid grid-cols-6 items-center gap-4 cursor-pointer hover:bg-gray-50 rounded"
  >
    <div
      @click="slaActiveScreen = { screen: 'view', data: data, fetchData: true }"
      class="w-full py-3 pl-2 col-span-5"
    >
      <div
        class="text-base text-ink-gray-7 font-medium flex items-center gap-2"
      >
        {{ data.name }}
        <Badge v-if="data.default_sla" color="gray" size="sm">Default</Badge>
      </div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-sm w-full text-ink-gray-5 mt-1 whitespace-nowrap overflow-ellipsis overflow-hidden"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="flex justify-between items-center w-full pr-2">
      <div>
        <Switch
          size="sm"
          :modelValue="data.enabled"
          @update:modelValue="onToggle"
        />
      </div>
      <div>
        <Dropdown
          placement="right"
          :options="[
            {
              label: 'Duplicate',
              onClick: () => {
                duplicateDialog = {
                  show: true,
                  name: props.data.name + ' (Copy)',
                };
              },
              icon: 'copy',
            },
            {
              label: 'Confirm Delete',
              component: (props) =>
                TemplateOption({
                  option: isConfirmingDelete ? 'Confirm Delete' : 'Delete',
                  icon: 'trash-2',
                  active: props.active,
                  variant: isConfirmingDelete ? 'danger' : 'gray',
                  onClick: (event) => deleteSla(event),
                }),
            },
          ]"
        >
          <Button
            icon="more-horizontal"
            variant="ghost"
            @click="isConfirmingDelete = false"
          />
        </Dropdown>
      </div>
    </div>
  </div>
  <Dialog
    :options="{ title: `Duplicate SLA Policy` }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          label="New SLA Policy Name"
          type="text"
          v-model="duplicateDialog.name"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          variant="subtle"
          label="Close"
          @click="duplicateDialog.show = false"
        />
        <Button variant="solid" label="Duplicate" @click="duplicate()" />
      </div>
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import {
  Switch,
  Button,
  Dropdown,
  createResource,
  toast,
  Dialog,
  Badge,
} from "frappe-ui";
import { ref } from "vue";
import { slaActiveScreen, slaPolicyListData } from "@/stores/sla";
import { TemplateOption } from "@/utils";

const duplicateDialog = ref({
  show: false,
  name: "",
});

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
      new_name: duplicateDialog.value.name,
    },
    onSuccess: (data) => {
      slaPolicyListData.reload();
      toast.success("SLA policy duplicated");
      duplicateDialog.value = {
        show: false,
        name: "",
      };
      slaActiveScreen.value = {
        screen: "view",
        data: data,
        fetchData: true,
      };
    },
    auto: true,
  });
};

const deleteSla = (event) => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
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
      toast.success("SLA policy deleted");
    },
    auto: true,
  });
};

const onToggle = () => {
  if (props.data.default_sla) {
    toast.error("SLA set as default cannot be disabled");
    return;
  }
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
      toast.success("SLA policy status updated");
    },
    auto: true,
  });
};
</script>
