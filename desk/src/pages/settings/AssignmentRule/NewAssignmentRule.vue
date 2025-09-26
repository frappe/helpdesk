<template>
  <SettingsHeader :routes="routes" />
  <div class="max-w-3xl xl:max-w-4xl mx-auto w-full p-4 lg:py-8">
    <div class="bg-white pb-6">
      <div class="flex flex-col sm:flex-row justify-between w-full gap-2">
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="
              assignmentRuleData.assignmentRuleName || __('New Assignment Rule')
            "
            size="md"
            @click="goBack()"
            class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-48 md:!max-w-60 lg:!max-w-max overflow-ellipsis overflow-hidden"
          />
          <Badge
            :variant="'subtle'"
            :theme="'orange'"
            size="sm"
            :label="__('Unsaved')"
            v-if="isDirty"
          />
        </div>
        <div class="flex items-center justify-between gap-4">
          <div
            class="flex items-center justify-between gap-2"
            @click="assignmentRuleData.disabled = !assignmentRuleData.disabled"
          >
            <Switch size="sm" :model-value="!assignmentRuleData.disabled" />
            <span class="text-sm text-ink-gray-7">{{ __("Enabled") }}</span>
          </div>
          <Button
            :disabled="Boolean(!isDirty)"
            :label="__('Save')"
            theme="gray"
            variant="solid"
            @click="saveAssignmentRule()"
            :loading="isLoading"
          />
        </div>
      </div>
    </div>
    <div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <FormControl
            :type="'text'"
            size="sm"
            variant="subtle"
            placeholder="Name"
            label="Name"
            v-model="assignmentRuleData.assignmentRuleName"
            required
            maxlength="55"
            @change="validateAssignmentRule('assignmentRuleName')"
          />
          <ErrorMessage
            :message="assignmentRulesErrors.assignmentRuleName"
            class="mt-2"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <FormLabel label="Priority" />
          <Popover>
            <template #target="{ togglePopover }">
              <div
                class="flex items-center justify-between text-base rounded h-7 py-1.5 pl-2 pr-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark] cursor-default"
                @click="togglePopover()"
              >
                <div>
                  {{
                    priorityOptions.find(
                      (option) => option.value == assignmentRuleData.priority
                    )?.label
                  }}
                </div>
                <FeatherIcon name="chevron-down" class="size-4" />
              </div>
            </template>
            <template #body="{ togglePopover }">
              <div
                class="p-1 text-ink-gray-6 top-1 absolute w-full bg-white shadow-2xl rounded"
              >
                <div
                  v-for="option in priorityOptions"
                  :key="option.value"
                  class="p-2 cursor-pointer hover:bg-gray-50 text-base flex items-center justify-between rounded"
                  @click="
                    assignmentRuleData.priority = option.value;
                    togglePopover();
                  "
                >
                  {{ option.label }}
                  <FeatherIcon
                    v-if="assignmentRuleData.priority == option.value"
                    name="check"
                    class="size-4"
                  />
                </div>
              </div>
            </template>
          </Popover>
        </div>
        <div>
          <FormControl
            :type="'textarea'"
            size="sm"
            variant="subtle"
            placeholder="Description"
            label="Description"
            required
            maxlength="250"
            @change="validateAssignmentRule('description')"
            v-model="assignmentRuleData.description"
          />
          <ErrorMessage
            :message="assignmentRulesErrors.description"
            class="mt-2"
          />
        </div>
      </div>
      <hr class="my-8" />
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold text-ink-gray-8">{{
            __("Assignment condition")
          }}</span>
          <div class="flex items-center justify-between gap-6">
            <span class="text-p-sm text-ink-gray-6">
              {{
                __("Choose which tickets are affected by this assignment rule.")
              }}
              <a
                class="font-medium underline"
                href="https://docs.frappe.io/helpdesk/assignment-rule"
                target="_blank"
                >{{ __("Learn about conditions") }}</a
              >
            </span>
            <div v-if="isOldSla">
              <Popover trigger="hover" :hoverDelay="0.25" placement="top-end">
                <template #target>
                  <div
                    class="text-sm text-ink-gray-6 flex gap-1 cursor-default text-nowrap items-center"
                  >
                    <span>{{ __("Old Condition") }}</span>
                    <FeatherIcon name="info" class="size-4" />
                  </div>
                </template>
                <template #body-main>
                  <div
                    class="text-sm text-ink-gray-6 p-2 bg-white rounded-md max-w-96 text-wrap whitespace-pre-wrap leading-5"
                  >
                    <code>{{ assignmentRuleData.assignCondition }}</code>
                  </div>
                </template>
              </Popover>
            </div>
          </div>
        </div>
        <div class="mt-5">
          <AssignmentRulesSection
            :conditions="assignmentRuleData.assignConditionJson"
            name="assignCondition"
            :errors="assignmentRulesErrors.assignConditionError"
          />
          <ErrorMessage
            :message="assignmentRulesErrors.assignCondition"
            class="mt-2"
          />
        </div>
      </div>
      <hr class="my-8" />
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold text-ink-gray-8">{{
            __("Unassignment condition")
          }}</span>
          <div class="flex items-center justify-between gap-6">
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  "Choose which tickets are affected by this un-assignment rule."
                )
              }}
              <a
                class="font-medium underline"
                href="https://docs.frappe.io/helpdesk/assignment-rule"
                target="_blank"
                >{{ __("Learn about conditions") }}</a
              >
            </span>
          </div>
        </div>
        <div class="mt-5">
          <AssignmentRulesSection
            :conditions="assignmentRuleData.unassignConditionJson"
            name="unassignCondition"
            :errors="assignmentRulesErrors.unassignConditionError"
          />
        </div>
      </div>
      <hr class="my-8" />
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold text-ink-gray-8">{{
            __("Assignment Schedule")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __("Choose the days of the week when this rule should be active.")
            }}
          </span>
        </div>
        <div class="mt-6">
          <AssignmentSchedule />
        </div>
      </div>
      <hr class="my-8" />
      <AssigneeRules />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import {
  Badge,
  Button,
  createResource,
  ErrorMessage,
  FormControl,
  FormLabel,
  Popover,
  Switch,
  toast,
} from "frappe-ui";
import { onUnmounted, ref, watch } from "vue";
import {
  assignmentRuleData,
  assignmentRulesErrors,
  resetAssignmentRuleData,
  resetAssignmentRuleErrors,
  validateAssignmentRule,
} from "@/stores/assignmentRules";
import AssigneeRules from "./components/AssigneeRules.vue";
import AssignmentRulesSection from "./components/AssignmentRulesSection.vue";
import AssignmentSchedule from "./components/AssignmentSchedule.vue";
import { convertToConditions } from "@/utils";
import { onBeforeRouteLeave, useRouter } from "vue-router";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";

const routes = computed(() => [
  {
    label: "Assignment Rules",
    route: "/settings/assignment-rules",
  },
  {
    label:
      assignmentRuleData.value?.assignmentRuleName || "New Assignment Rule",
    route: "/settings/assignment-rules/new",
  },
]);

const { $dialog } = globalStore();

const isDirty = ref(false);
const initialData = ref(JSON.stringify(assignmentRuleData.value));
const isLoading = ref(false);
const router = useRouter();
const useNewUI = ref(true);
const isOldSla = ref(false);

const goBack = () => {
  router.push({ name: "AssignmentRules" });
};

const saveAssignmentRule = () => {
  const validationErrors = validateAssignmentRule(undefined, !useNewUI.value);

  if (Object.values(validationErrors).some((error) => error)) {
    toast.error(
      __("Invalid fields, check if all are filled in and values are correct.")
    );
    return;
  }

  createAssignmentRule();
};

const createAssignmentRule = () => {
  isLoading.value = true;
  createResource({
    url: "frappe.client.insert",
    params: {
      doc: {
        doctype: "Assignment Rule",
        document_type: "HD Ticket",
        rule: assignmentRuleData.value.rule,
        priority: assignmentRuleData.value.priority,
        users: assignmentRuleData.value.users,
        disabled: assignmentRuleData.value.disabled,
        description: assignmentRuleData.value.description,
        assignment_days: assignmentRuleData.value.assignmentDays.map((day) => ({
          day: day,
        })),
        name: assignmentRuleData.value.assignmentRuleName,
        assignment_rule_name: assignmentRuleData.value.assignmentRuleName,
        assign_condition: convertToConditions({
          conditions: assignmentRuleData.value.assignConditionJson,
        }),
        unassign_condition: convertToConditions({
          conditions: assignmentRuleData.value.unassignConditionJson,
        }),
        assign_condition_json: JSON.stringify(
          assignmentRuleData.value.assignConditionJson
        ),
        unassign_condition_json: JSON.stringify(
          assignmentRuleData.value.unassignConditionJson
        ),
      },
    },
    auto: true,
    onSuccess(data) {
      toast.success(__("Assignment rule created"));
      isDirty.value = false;
      router.push({ name: "EditAssignmentRule", params: { id: data.name } });
    },
    onError: () => {
      isLoading.value = false;
    },
  });
};

const priorityOptions = [
  { label: "Low", value: "0" },
  { label: "Low-Medium", value: "1" },
  { label: "Medium", value: "2" },
  { label: "Medium-High", value: "3" },
  { label: "High", value: "4" },
];

watch(
  assignmentRuleData,
  (newVal) => {
    if (!initialData.value) return;
    isDirty.value = JSON.stringify(newVal) != initialData.value;
  },
  { deep: true }
);

const confirmLeave = () => {
  return new Promise<boolean>((resolve) => {
    $dialog({
      title: __("Unsaved changes"),
      message: __(
        "Are you sure you want to leave? Unsaved changes will be lost."
      ),
      actions: [
        {
          label: __("Confirm"),
          variant: "solid",
          onClick: (close: Function) => {
            resolve(true);
            close();
          },
        },
        {
          label: __("Cancel"),
          variant: "ghost",
          onClick: (close: Function) => {
            resolve(false);
            close();
          },
        },
      ],
    });
  });
};

onBeforeRouteLeave(async (to, from, next) => {
  if (isDirty.value) {
    const confirmed = await confirmLeave();
    if (confirmed) {
      next();
    } else {
      next(false);
    }
  } else {
    next();
  }
});

onUnmounted(() => {
  resetAssignmentRuleErrors();
  resetAssignmentRuleData();
});
</script>
