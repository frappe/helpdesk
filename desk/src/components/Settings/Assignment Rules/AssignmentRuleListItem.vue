<template>
  <div
    class="grid grid-cols-12 items-center gap-4 cursor-pointer hover:bg-gray-50 rounded"
  >
    <div
      @click="assignmentRulesActiveScreen = { screen: 'view', data: data }"
      class="w-full pl-2 col-span-7 h-14 flex flex-col justify-center"
    >
      <div class="text-base text-ink-gray-7 font-medium">{{ data.name }}</div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-sm w-full text-ink-gray-5 mt-1 truncate"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="col-span-3">
      <select
        class="w-full h-7 text-base hover:bg-surface-gray-3 rounded-md p-0 pl-2 pr-5 bg-transparent -ml-2 border-0 text-ink-gray-8 focus-visible:!ring-0 bg-none truncate"
        v-model="data.priority"
        @update:modelValue="onPriorityChange"
        @change="onPriorityChange"
      >
        <option
          v-for="option in priorityOptions"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>
    </div>
    <div class="flex justify-between items-center w-full pr-2 col-span-2">
      <div>
        <Switch
          size="sm"
          :modelValue="!data.disabled"
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
    :options="{ title: __('Duplicate Assignment Rule') }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :label="__('New Assignment Rule Name')"
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
import { assignmentRulesActiveScreen } from "@/stores/assignmentRules";
import { __ } from "@/translation";
import { AssignmentRuleListResourceSymbol } from "@/types";
import { AssignmentRule } from "@/types/doctypes";
import { ConfirmDelete } from "@/utils";
import {
  Button,
  createResource,
  Dialog,
  Dropdown,
  FormControl,
  Switch,
  toast,
} from "frappe-ui";
import { inject, ref } from "vue";

const assignmentRulesListData = inject(AssignmentRuleListResourceSymbol);

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const priorityOptions = [
  { label: "Low", value: "0" },
  { label: "Low-Medium", value: "1" },
  { label: "Medium", value: "2" },
  { label: "Medium-High", value: "3" },
  { label: "High", value: "4" },
];

const duplicateDialog = ref({
  show: false,
  newName: "",
  name: "",
});

const isConfirmingDelete = ref(false);

const deleteAssignmentRule = () => {
  createResource({
    url: "frappe.client.delete",
    params: {
      doctype: "Assignment Rule",
      name: props.data.name,
    },
    onSuccess: () => {
      assignmentRulesListData?.reload();
      isConfirmingDelete.value = false;
      toast.success(__("Assignment rule deleted"));
    },
    auto: true,
  });
};

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
    onConfirmDelete: () => deleteAssignmentRule(),
    isConfirmingDelete,
  }),
];

const duplicate = () => {
  createResource({
    url: "frappe.client.get",
    params: {
      doctype: "Assignment Rule",
      name: duplicateDialog.value.name,
    },
    onSuccess: (data: AssignmentRule) => {
      createResource({
        url: "frappe.client.insert",
        params: {
          doc: {
            ...data,
            name: duplicateDialog.value.newName,
          },
        },
        auto: true,
        onSuccess(newAssignmentRuleData: AssignmentRule) {
          assignmentRulesListData?.reload();
          toast.success(__("Assignment rule duplicated"));
          duplicateDialog.value = {
            show: false,
            newName: "",
            name: "",
          };
          setTimeout(() => {
            assignmentRulesActiveScreen.value = {
              screen: "view",
              data: newAssignmentRuleData,
            };
          }, 250);
        },
      });
    },
    auto: true,
  });
};

const onPriorityChange = () => {
  setAssignmentRuleValue("priority", props.data.priority);
};

const onToggle = () => {
  if (!props.data.users_exists && props.data.disabled) {
    toast.error(__("Cannot enable rule without adding users in it"));
    return;
  }
  setAssignmentRuleValue("disabled", !props.data.disabled, "status");
};

const setAssignmentRuleValue = (
  key: string,
  value: any,
  fieldName?: string
) => {
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "Assignment Rule",
      name: props.data.name,
      fieldname: key,
      value: value,
    },
    onSuccess: () => {
      assignmentRulesListData?.reload();
      toast.success(__("Assignment rule {0} updated", fieldName || key));
    },
    auto: true,
  });
};
</script>
