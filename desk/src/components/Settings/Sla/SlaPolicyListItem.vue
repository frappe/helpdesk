<template>
  <div
    class="grid grid-cols-6 items-center gap-4 cursor-pointer hover:bg-gray-50 rounded"
  >
    <div
      @click="slaActiveScreen = { screen: 'view', data: data, fetchData: true }"
      class="w-full pl-2 col-span-5 flex flex-col justify-center h-14"
    >
      <div
        class="text-base text-ink-gray-7 font-medium flex items-center gap-2"
      >
        {{ data.name }}
        <Badge v-if="data.default_sla" color="gray" size="sm">Default</Badge>
      </div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-sm w-full text-ink-gray-5 mt-1 truncate"
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
        <Dropdown placement="right" :options="dropdownOptions">
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
    :options="{ title: __('Duplicate SLA Policy') }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :label="__('New SLA Policy Name')"
          type="text"
          v-model="duplicateDialog.newName"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          variant="subtle"
          :label="__('Close')"
          @click="duplicateDialog.show = false"
        />
        <Button variant="solid" :label="__('Duplicate')" @click="duplicate()" />
      </div>
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import {
  Switch,
  Button,
  createResource,
  toast,
  Dialog,
  Badge,
  Dropdown,
} from "frappe-ui";
import { ref, inject } from "vue";
import { slaActiveScreen } from "@/stores/sla";
import { ConfirmDelete } from "@/utils";
import { __ } from "@/translation";
import { SlaPolicyListResourceSymbol } from "@/types";
import { HDServiceLevelAgreement } from "@/types/doctypes";

const slaPolicyList = inject(SlaPolicyListResourceSymbol);

const duplicateDialog = ref({
  show: false,
  newName: "",
  name: "",
});

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const isConfirmingDelete = ref(false);

const dropdownOptions = [
  {
    label: __("Duplicate"),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        newName: props.data.name + " (Copy)",
        name: props.data.name,
      };
    },
    icon: "copy",
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteSla(),
    isConfirmingDelete,
  }),
];

const duplicate = () => {
  createResource({
    url: "frappe.client.get",
    params: {
      doctype: "HD Service Level Agreement",
      name: duplicateDialog.value.name,
    },
    onSuccess: (data: HDServiceLevelAgreement) => {
      createResource({
        url: "frappe.client.insert",
        params: {
          doc: {
            ...data,
            default_sla: false,
            service_level: duplicateDialog.value.newName,
            name: duplicateDialog.value.newName,
          },
        },
        auto: true,
        onSuccess(newSlaPolicyData: HDServiceLevelAgreement) {
          slaPolicyList?.reload();
          toast.success(__("SLA policy duplicated"));
          duplicateDialog.value = {
            show: false,
            newName: "",
            name: "",
          };
          setTimeout(() => {
            slaActiveScreen.value = {
              screen: "view",
              data: newSlaPolicyData,
              fetchData: true,
            };
          }, 250);
        },
      });
    },
    auto: true,
  });
};

const deleteSla = () => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  slaPolicyList?.delete.submit(props.data.name, {
    onSuccess: () => {
      toast.success(__("SLA policy deleted"));
    },
  });
};

const onToggle = () => {
  if (props.data.default_sla) {
    toast.error(__("SLA set as default cannot be disabled"));
    return;
  }
  slaPolicyList?.setValue.submit(
    {
      name: props.data.name,
      enabled: !props.data.enabled,
    },
    {
      onSuccess: () => {
        toast.success(__("SLA policy status updated"));
      },
    }
  );
};
</script>
