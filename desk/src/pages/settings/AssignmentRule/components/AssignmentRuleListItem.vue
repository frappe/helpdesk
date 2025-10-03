<template>
  <div
    class="grid grid-cols-8 sm:grid-cols-11 items-center gap-4 cursor-pointer group rounded relative my-1"
  >
    <div
      @click="
        router.push({
          name: 'EditAssignmentRule',
          params: { id: data.name },
        })
      "
      class="w-full col-span-3 sm:col-span-7 flex flex-col justify-center h-12.5"
    >
      <div class="text-base text-ink-gray-7 font-medium">{{ data.name }}</div>
      <div
        v-if="data.description && data.description.length > 0"
        class="text-sm w-full text-ink-gray-5 mt-1 whitespace-nowrap overflow-ellipsis overflow-hidden"
      >
        {{ data.description }}
      </div>
    </div>
    <div class="col-span-3 sm:col-span-2">
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
        <Dropdown :options="dropdownOptions">
          <Button
            icon="more-horizontal"
            variant="ghost"
            @click="isConfirmingDelete = false"
          />
        </Dropdown>
      </div>
    </div>
    <div
      class="absolute -left-2.5 -top-1 w-full h-full group-hover:bg-gray-50 rounded-md z-[-1]"
      :style="{
        width: 'calc(100% + 20px)',
        height: 'calc(100% + 8px)',
      }"
    />
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
          v-model="duplicateDialog.name"
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
import { ConfirmDelete } from "@/utils";
import {
  Button,
  createResource,
  Dialog,
  FormControl,
  Select,
  Switch,
  toast,
} from "frappe-ui";
import { inject, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const assignmentRulesList = inject<any>("assignmentRulesList");

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
      assignmentRulesList.reload();
      isConfirmingDelete.value = false;
      toast.success(__("Assignment rule deleted"));
    },
    auto: true,
  });
};

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
  ...ConfirmDelete({
    onConfirmDelete: () => deleteAssignmentRule(),
    isConfirmingDelete,
  }),
];

const duplicate = () => {
  createResource({
    url: "helpdesk.api.assignment_rule.duplicate_assignment_rule",
    params: {
      docname: props.data.name,
      new_name: duplicateDialog.value.name,
    },
    onSuccess: (data) => {
      assignmentRulesList.reload();
      toast.success(__("Assignment rule duplicated"));
      duplicateDialog.value.show = false;
      duplicateDialog.value.name = "";
      assignmentRulesActiveScreen.value = {
        screen: "view",
        data: {
          name: data.name,
        },
      };
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

const setAssignmentRuleValue = (key, value, fieldName = undefined) => {
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "Assignment Rule",
      name: props.data.name,
      fieldname: key,
      value: value,
    },
    onSuccess: () => {
      assignmentRulesList.reload();
      toast.success(__("Assignment rule {0} updated", fieldName || key));
    },
    auto: true,
  });
};
</script>
