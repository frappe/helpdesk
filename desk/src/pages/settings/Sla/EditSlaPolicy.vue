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
            class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-xl hover:opacity-70 !pr-0 max-w-48 md:max-w-60 lg:max-w-max overflow-ellipsis overflow-hidden"
          />
          <Badge
            :variant="'subtle'"
            :theme="'orange'"
            size="sm"
            label="Unsaved changes"
            v-if="isSlaDataDirty"
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
            :disabled="Boolean(!isSlaDataDirty)"
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
            :disabled="true"
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
            <div v-if="isOldSla && !slaData.default_sla">
              <Popover trigger="hover" :hoverDelay="0.25" placement="top-end">
                <template #target>
                  <div
                    class="text-sm text-ink-gray-6 flex gap-1 cursor-default"
                  >
                    Old Conditions
                    <FeatherIcon name="info" class="size-4" />
                  </div>
                </template>
                <template #body-main>
                  <div
                    class="text-sm text-ink-gray-6 p-2 bg-white rounded-md max-w-96 text-wrap whitespace-pre-wrap leading-5"
                  >
                    <code>{{ slaData.condition }}</code>
                  </div>
                </template>
              </Popover>
            </div>
          </div>
          <div class="mt-5" v-if="!slaData.default_sla">
            <div
              class="flex flex-col gap-3 items-center text-center text-ink-gray-7 text-sm mb-2 border border-gray-300 rounded-md p-3 py-4"
              v-if="!useNewUI"
            >
              <span class="text-p-sm">
                Conditions for this SLA were created from
                <a :href="deskUrl" target="_blank" class="underline">desk</a>
                which are not compatible with this UI, you will need to recreate
                the conditions here if you want to manage and add new conditions
                from this UI.
              </span>
              <Button
                label="I understand, add conditions"
                variant="subtle"
                theme="gray"
                @click="useNewUI = true"
              />
            </div>
            <SlaAssignmentConditions
              :conditions="slaData.condition_json"
              v-if="useNewUI"
            />
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
  </div>
</template>

<script setup lang="ts">
import { computed, provide } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import {
  isSlaDataDirty,
  resetSlaDataErrors,
  slaData,
  slaDataErrors,
  slaInitialData,
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
  Popover,
  Switch,
  toast,
} from "frappe-ui";
import { nextTick, onUnmounted, ref, watch } from "vue";
import SlaAssignmentConditions from "./components/SlaAssignmentConditions.vue";
import SlaHolidays from "./components/SlaHolidays.vue";
import SlaPriorityList from "./components/SlaPriorityList.vue";
import SlaStatusList from "./components/SlaStatusList.vue";
import { useRouter, onBeforeRouteLeave } from "vue-router";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
const { $dialog } = globalStore();

const useNewUI = ref(true);
const isOldSla = ref(false);
const isEditingHolidayList = ref(false);

provide("isEditingHolidayList", isEditingHolidayList);

const router = useRouter();

const deskUrl = `${window.location.origin}/app/hd-service-level-agreement/${router.currentRoute.value.params.id}`;
const fetchData = ref(
  router.currentRoute.value.query.fetchData === undefined ||
    router.currentRoute.value.query.fetchData === "true"
);

const getSlaData = createResource({
  url: "helpdesk.api.sla.get_sla",
  params: {
    docname: router.currentRoute.value.params.id,
  },
  onSuccess(data) {
    const condition_json = JSON.parse(data.condition_json || "[]");

    const newData = {
      ...data,
      loading: false,
      condition_json: condition_json,
    };
    slaData.value = newData;
    slaData.value.apply_sla_for_resolution = true;
    slaInitialData.value = JSON.stringify(slaData.value);
    const conditionsAvailable = slaData.value.condition?.length > 0;
    const conditionsJsonAvailable = slaData.value.condition_json?.length > 0;
    if (conditionsAvailable && !conditionsJsonAvailable) {
      useNewUI.value = false;
      isOldSla.value = true;
    } else {
      useNewUI.value = true;
      isOldSla.value = false;
    }
  },
});

if (Boolean(fetchData.value)) {
  getSlaData.fetch();
} else {
  // Clear fetchData query param
  const currentRoute = router.currentRoute.value;
  const query = { ...currentRoute.query };
  delete query.fetchData;
  router.replace({
    ...currentRoute,
    query,
  });
}

const routes = computed(() => [
  {
    label: "SLA Policies",
    route: "/settings/sla-policies",
  },
  {
    label: slaData.value.service_level,
    route: `/settings/sla-policies/${slaData.value.name}`,
  },
]);

const goBack = () => {
  router.push({ name: "SLAPolicies" });
};

const saveSla = () => {
  const validationErrors = validateSlaData(undefined, !useNewUI.value);

  if (Object.values(validationErrors).some((error) => error)) {
    toast.error(
      __("Invalid fields, check if all are filled in and values are correct.")
    );
    return;
  }
  if (isOldSla.value && useNewUI.value) {
    $dialog({
      title: __("Confirm overwrite"),
      message: __(
        "Your old conditions will be overwritten. Are you sure you want to save?"
      ),
      actions: [
        {
          label: "Save",
          variant: "solid",
          onClick: (close: Function) => {
            updateSla();
            close();
          },
        },
        {
          label: "Cancel",
          onClick: (close: Function) => {
            close();
          },
        },
      ],
    });
    return;
  }
  updateSla();
};

const updateSla = () => {
  const defaultTicketStatus = slaData.value.default_ticket_status
    ? slaData.value.default_ticket_status
    : null;
  const ticketReopenStatus = slaData.value.ticket_reopen_status
    ? slaData.value.ticket_reopen_status
    : null;
  createResource({
    url: "frappe.client.set_value",
    auto: true,
    params: {
      doctype: "HD Service Level Agreement",
      name: router.currentRoute.value.params.id,
      fieldname: {
        ...slaData.value,
        name: router.currentRoute.value.params.id,
        default_ticket_status: defaultTicketStatus,
        ticket_reopen_status: ticketReopenStatus,
        condition: useNewUI.value
          ? convertToConditions({
              conditions: slaData.value.condition_json,
              fieldPrefix: "doc",
            })
          : slaData.value.condition,
        condition_json: useNewUI.value
          ? JSON.stringify(slaData.value.condition_json)
          : null,
      },
    },
    onSuccess() {
      getSlaData.submit();
      toast.success("SLA policy updated");
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
    if (!slaInitialData.value) return;
    isSlaDataDirty.value = JSON.stringify(newVal) != slaInitialData.value;
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
  if (isSlaDataDirty.value && !isEditingHolidayList.value) {
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
