<template>
  <div
    class="grid grid-cols-11 items-center gap-4 cursor-pointer hover:bg-gray-50 rounded"
  >
    <div
      @click="assignmentRulesActiveScreen = { screen: 'view', data: data }"
      class="w-full py-3 pl-2 col-span-7"
    >
      <div class="text-base text-ink-gray-7 font-medium">{{ data.name }}</div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-sm w-full text-ink-gray-5 mt-1 whitespace-nowrap overflow-ellipsis overflow-hidden"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="col-span-2">
      <Select
        class="w-max bg-transparent -ml-2 border-0 text-ink-gray-6 focus-visible:!ring-0 bg-none"
        :options="priorityOptions"
        v-model="data.priority"
        @update:modelValue="onPriorityChange"
      />
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
    :options="{ title: `Duplicate Assignment Rule` }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          label="New Assignment Rule Name"
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
import { assignmentRulesActiveScreen } from "@/stores/assignmentRules";
import { TemplateOption } from "@/utils";
import {
  Button,
  createResource,
  Dropdown,
  Select,
  Switch,
  toast,
} from "frappe-ui";
import { inject, ref } from "vue";

const assignmentRulesList = inject<any>("assignmentRulesList");

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const priorityOptions = [
  { label: "Low", value: "0" },
  { label: "Medium-Low", value: "1" },
  { label: "Medium", value: "2" },
  { label: "Medium-High", value: "3" },
  { label: "High", value: "4" },
];

const duplicateDialog = ref({
  show: false,
  name: "",
});

const isConfirmingDelete = ref(false);

const dropdownOptions = [
  {
    label: "Duplicate",
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: props.data.name + " (Copy)",
      };
    },
    icon: "copy",
  },
  {
    label: "Delete",
    component: (props) =>
      TemplateOption({
        option: "Delete",
        icon: "trash-2",
        active: props.active,
        variant: "gray",
        onClick: (event) => deleteAssignmentRule(event),
      }),
    condition: () => !isConfirmingDelete.value,
  },
  {
    label: "Confirm Delete",
    component: (props) =>
      TemplateOption({
        option: "Confirm Delete",
        icon: "trash-2",
        active: props.active,
        variant: "danger",
        onClick: (event) => deleteAssignmentRule(event),
      }),
    condition: () => isConfirmingDelete.value,
  },
];

const duplicate = () => {
  createResource({
    url: "frappe.client.insert",
    params: {
      doctype: "Assignment Rule",
      doc: {
        ...props.data,
        name: duplicateDialog.value.name,
      },
    },
    onSuccess: () => {
      assignmentRulesList.reload();
      toast.success("Assignment rule duplicated");
      duplicateDialog.value.show = false;
      duplicateDialog.value.name = "";
    },
    auto: true,
  });
};

const deleteAssignmentRule = (event) => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }
  createResource({
    url: "frappe.client.delete",
    params: {
      doctype: "Assignment Rule",
      name: props.data.name,
    },
    onSuccess: () => {
      assignmentRulesList.reload();
      isConfirmingDelete.value = false;
      toast.success("Assignment rule deleted");
    },
    auto: true,
  });
};

const onPriorityChange = () => {
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "Assignment Rule",
      name: props.data.name,
      fieldname: "priority",
      value: props.data.priority,
    },
    onSuccess: () => {
      assignmentRulesList.reload();
      toast.success("Assignment rule priority updated");
    },
    auto: true,
  });
};

const onToggle = () => {
  if (props.data.users.length == 0 && props.data.disabled) {
    toast.error("Cannot enable rule without adding users in it");
    return;
  }
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "Assignment Rule",
      name: props.data.name,
      fieldname: "disabled",
      value: !props.data.disabled,
    },
    onSuccess: () => {
      assignmentRulesList.reload();
      toast.success("Assignment rule status updated");
    },
    auto: true,
  });
};
</script>
