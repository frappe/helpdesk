<template>
  <div
    class="grid grid-cols-12 items-center gap-4 cursor-pointer hover:bg-surface-menu-bar rounded"
  >
    <div
      @click="assignmentRulesActiveScreen = { screen: 'view', data: data }"
      class="w-full ps-2 col-span-7 h-14 flex flex-col justify-center"
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
        class="w-full h-7 text-base hover:bg-surface-gray-3 rounded-md p-0 ps-2 pe-5 bg-transparent -ms-2 border-0 text-ink-gray-8 focus-visible:!ring-0 bg-none truncate"
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
    <div class="flex justify-between items-center w-full pe-2 col-span-2">
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
            icon="lucide-more-horizontal"
            variant="ghost"
            @click="isConfirmingDelete = false"
          />
        </Dropdown>
      </div>
    </div>
  </div>
  <Dialog
    :title="__('Duplicate Assignment Rule')"
    v-model:open="duplicateDialog.show"
  >
    <template #default>
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
      toast.success(__("Assignment rule deleted successfully."));
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
    icon: "lucide-copy",
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
          toast.success(__("Assignment rule duplicated successfully."));
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

const onToggle = (enabled: boolean) => {
  if (!props.data.users_exists && props.data.disabled) {
    toast.error(__("Cannot enable rule without adding users in it"));
    return;
  }
  // Optimistically flip so the switch reflects the new state immediately;
  // revert if the backend update fails.
  const previous = props.data.disabled;
  props.data.disabled = enabled ? 0 : 1;
  setAssignmentRuleValue("disabled", props.data.disabled, "status", () => {
    props.data.disabled = previous;
  });
};

const setAssignmentRuleValue = (
  key: string,
  value: any,
  fieldName?: string,
  onError?: () => void
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
      toast.success(
        __("Assignment rule {0} updated successfully.", fieldName || key)
      );
    },
    onError: () => {
      onError?.();
      toast.error(
        __("Failed to update assignment rule {0}.", fieldName || key)
      );
    },
    auto: true,
  });
};
</script>
