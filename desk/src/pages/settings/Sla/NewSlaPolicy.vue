<template>
  <SettingsHeader :routes="routes" />
  <div class="max-w-3xl xl:max-w-4xl mx-auto w-full p-4 lg:py-8">
    <div v-if="slaData.loading" class="flex items-center h-full justify-center">
      <LoadingIndicator class="w-4" />
    </div>
    <div v-if="!slaData.loading" class="bg-white pb-6">
      <div class="flex flex-col sm:flex-row justify-between w-full gap-2">
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="slaData.service_level || 'New SLA Policy'"
            size="md"
            @click="goBack()"
            class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-xl hover:opacity-70 !pr-0 !max-w-48 md:!max-w-60 lg:!max-w-max overflow-ellipsis overflow-hidden"
          />
          <Badge
            :variant="'subtle'"
            :theme="'orange'"
            size="sm"
            label="Unsaved changes"
            v-if="isDirty"
          />
        </div>
        <div class="flex gap-4 items-center justify-between">
          <div
            class="flex items-center justify-between gap-2 cursor-pointer flex-row-reverse"
            @click="toggleEnabled"
          >
            <Switch size="sm" v-model="slaData.enabled" />
            <span class="text-sm text-ink-gray-7 font-medium">Enabled</span>
          </div>
          <Button
            label="Save"
            theme="gray"
            variant="solid"
            @click="saveSla()"
            :disabled="Boolean(!isDirty)"
            :loading="slaData.loading"
          />
        </div>
      </div>
    </div>
    <div v-if="!slaData.loading" class="overflow-y-auto">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <FormControl
            :type="'text'"
            size="sm"
            variant="subtle"
            placeholder="Name"
            label="Name"
            v-model="slaData.service_level"
            required
            @change="validateSlaData('service_level')"
            :maxlength="55"
          />
          <ErrorMessage :message="slaDataErrors.service_level" class="mt-2" />
        </div>
        <FormControl
          :type="'textarea'"
          size="sm"
          variant="subtle"
          placeholder="Description"
          label="Description"
          v-model="slaData.description"
        />
      </div>
      <hr class="my-8" />
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold text-ink-gray-8"
            >Assignment conditions</span
          >
          <span class="text-p-sm text-ink-gray-6">
            Choose which tickets are affected by this policy.
          </span>
        </div>
        <div class="mt-3">
          <div class="flex items-center justify-between">
            <Checkbox
              label="Set as default SLA"
              :model-value="slaData.default_sla"
              @update:model-value="toggleDefaultSla"
              class="text-ink-gray-6 text-base font-medium"
            />
          </div>
          <div class="mt-5" v-if="!slaData.default_sla">
            <SlaAssignmentConditions :conditions="slaData.condition_json" />
          </div>
        </div>
      </div>
      <hr class="my-8" />
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold text-ink-gray-8">Valid from</span>
          <span class="text-p-sm text-ink-gray-6">
            Choose how long this SLA policy will be active.
          </span>
        </div>
        <div class="mt-3.5 flex gap-5 flex-col md:flex-row">
          <div class="w-full space-y-1.5">
            <FormLabel label="From date" for="from_date" />
            <DatePicker
              v-model="slaData.start_date"
              variant="subtle"
              placeholder="11/01/2025"
              class="w-full"
              id="from_date"
              @change="validateSlaData('start_date')"
              :formatter="(date) => getFormattedDate(date)"
            >
              <template #prefix>
                <LucideCalendar class="size-4" />
              </template>
            </DatePicker>
            <ErrorMessage :message="slaDataErrors.start_date" />
          </div>
          <div class="w-full space-y-1.5">
            <FormLabel label="To date" for="to_date" />
            <DatePicker
              v-model="slaData.end_date"
              variant="subtle"
              placeholder="25/12/2025"
              class="w-full"
              id="to_date"
              @change="validateSlaData('end_date')"
              :formatter="(date) => getFormattedDate(date)"
            >
              <template #prefix>
                <LucideCalendar class="size-4" />
              </template>
            </DatePicker>
            <ErrorMessage :message="slaDataErrors.end_date" />
          </div>
        </div>
      </div>
      <hr class="my-8" />
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold text-ink-gray-8"
            >Response and resolution</span
          >
          <span class="text-p-sm text-ink-gray-6">
            Add time targets around support milestones like first reply and
            resolution times
          </span>
        </div>
        <div class="mt-5">
          <!-- <div class="flex gap-6">
          <div
            class="flex items-center gap-2"
            @click="onApplySlaForChange(false)"
          >
            <input
              name="apply_sla_for"
              :checked="!slaData.apply_sla_for_resolution"
              type="radio"
            />
            <div class="select-none text-ink-gray-6 text-sm font-medium">
              Apply SLA for response time
            </div>
          </div>
          <div
            class="flex items-center gap-2"
            @click="onApplySlaForChange(true)"
          >
            <input
              name="apply_sla_for"
              :checked="slaData.apply_sla_for_resolution"
              type="radio"
            />
            <div class="select-none text-ink-gray-6 text-sm font-medium">
              Apply SLA for response time and resolution time
            </div>
          </div>
        </div> -->
          <div class="mt-5">
            <SlaPriorityList />
          </div>
        </div>
      </div>
      <hr class="my-8" />
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold text-ink-gray-8"
            >Status details</span
          >
          <span class="text-p-sm text-ink-gray-6">
            Set the default status assigned when a ticket is created, and the
            status to apply when a ticket is reopened. If not specified, the
            default status from HD Settings will be used.
          </span>
        </div>
        <div class="mt-5">
          <SlaStatusList />
        </div>
      </div>
      <hr class="my-8" />
      <SlaHolidays />
    </div>
    <ConfirmDialog
      v-model="showConfirmDialog.show"
      :title="showConfirmDialog.title"
      :message="showConfirmDialog.message"
      :onConfirm="showConfirmDialog.onConfirm"
      :onCancel="() => (showConfirmDialog.show = false)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";

import ConfirmDialog from "@/components/ConfirmDialog.vue";
import {
  resetSlaData,
  resetSlaDataErrors,
  slaData,
  slaDataErrors,
  validateSlaData,
} from "@/stores/sla";
import { convertToConditions, getFormattedDate } from "@/utils";
import {
  Badge,
  Button,
  Checkbox,
  createResource,
  DatePicker,
  ErrorMessage,
  FormControl,
  FormLabel,
  LoadingIndicator,
  Switch,
  toast,
} from "frappe-ui";
import { nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import SlaAssignmentConditions from "./components/SlaAssignmentConditions.vue";
import SlaHolidays from "./components/SlaHolidays.vue";
import SlaPriorityList from "./components/SlaPriorityList.vue";
import SlaStatusList from "./components/SlaStatusList.vue";
import { useOnboarding } from "frappe-ui/frappe";
import { onBeforeRouteLeave, useRouter } from "vue-router";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";

const { $dialog } = globalStore();

const { updateOnboardingStep } = useOnboarding("helpdesk");

const showConfirmDialog = ref({
  show: false,
  title: "",
  message: "",
  onConfirm: () => {},
});
const isDirty = ref(false);
const initialData = ref(null);

const router = useRouter();

const routes = computed(() => [
  {
    label: "SLA Policies",
    route: "/settings/sla-policies",
  },
  {
    label: slaData.value.service_level || "New SLA Policy",
    route: "/settings/sla-policies/new",
  },
]);

const goBack = () => {
  router.push({ name: "SLAPolicies" });
};

const saveSla = () => {
  const validationErrors = validateSlaData(undefined, false);

  if (Object.values(validationErrors).some((error) => error)) {
    toast.error(
      "Invalid fields, check if all are filled in and values are correct."
    );
    return;
  }

  createSla();
};

const createSla = () => {
  const defaultTicketStatus = slaData.value.default_ticket_status
    ? slaData.value.default_ticket_status
    : null;
  const ticketReopenStatus = slaData.value.ticket_reopen_status
    ? slaData.value.ticket_reopen_status
    : null;

  createResource({
    url: "frappe.client.insert",
    auto: true,
    params: {
      doc: {
        doctype: "HD Service Level Agreement",
        ...slaData.value,
        default_ticket_status: defaultTicketStatus,
        ticket_reopen_status: ticketReopenStatus,
        condition: convertToConditions({
          conditions: slaData.value.condition_json,
          fieldPrefix: "doc",
        }),
        condition_json: JSON.stringify(slaData.value.condition_json),
      },
    },
    onSuccess(data) {
      toast.success("SLA policy created");
      isDirty.value = false;
      router.push({ name: "EditSLAPolicy", params: { id: data.name } });
      updateOnboardingStep("setup_sla", true);
    },
  });
};

const toggleEnabled = () => {
  if (slaData.value.default_sla) {
    toast.error("SLA set as default cannot be disabled");
    return;
  }
  slaData.value.enabled = !slaData.value.enabled;
};

const toggleDefaultSla = () => {
  slaData.value.default_sla = !slaData.value.default_sla;
  if (slaData.value.default_sla) {
    slaData.value.enabled = true;
  }
};

const onApplySlaForChange = (applyForResolution: boolean) => {
  slaData.value.apply_sla_for_resolution = applyForResolution;
  nextTick(() => {
    validateSlaData("priorities");
  });
};

watch(
  slaData,
  (newVal) => {
    // Set initial data when all the state changes are done
    if (!initialData.value && slaData.value.priorities.length > 0) {
      initialData.value = JSON.stringify(newVal);
      return;
    }
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
          label: "Confirm",
          variant: "solid",
          onClick: (close: Function) => {
            resolve(true);
            close();
          },
        },
        {
          label: "Cancel",
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

onMounted(() => {
  resetSlaData();
});

onUnmounted(() => {
  resetSlaDataErrors();
});
</script>

<style scoped>
input[type="radio"] {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  border: 2px solid #c5c2c2;
  border-radius: 50%;
  outline: none;
  transition: all 0.2s ease;
  background-color: white;
}

input[type="radio"]:checked {
  background-color: black;
  border: 2px solid #000;
}

input[type="radio"]:checked::after {
  content: "";
  background-color: #fff;
}

input[type="radio"]:focus {
  outline: none !important;
  box-shadow: none !important;
}
</style>
