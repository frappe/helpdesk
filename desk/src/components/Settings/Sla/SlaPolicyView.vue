<template>
  <div v-if="slaData.loading" class="flex items-center h-full justify-center">
    <Spinner class="w-8" />
  </div>
  <div
    v-if="!slaData.loading"
    class="sticky top-0 z-10 bg-white px-10 pt-8 pb-6"
  >
    <div class="flex items-center justify-between w-full">
      <div>
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="slaData.service_level || 'New SLA Policy'"
            size="md"
            @click="goBack()"
            class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5"
          />
          <Badge
            :variant="'subtle'"
            :theme="slaData.enabled ? 'blue' : 'gray'"
            size="sm"
            :label="slaData.enabled ? 'Enabled' : 'Disabled'"
          />
        </div>
      </div>
      <Button label="Save" theme="gray" variant="solid" @click="saveSla()" />
    </div>
  </div>
  <div v-if="!slaData.loading" class="overflow-y-auto px-10 pb-10">
    <div
      class="flex items-center justify-between gap-2"
      @click="slaData.enabled = !slaData.enabled"
    >
      <span class="text-sm"> Enable Policy </span>
      <Switch size="sm" :model-value="slaData.enabled" />
    </div>
    <hr class="mb-6 mt-3" />
    <div class="grid grid-cols-2 gap-2">
      <div>
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Name"
          label="Name"
          v-model="slaData.service_level"
          required
          @change="debouncedValidateSlaData()"
        />
        <span v-if="slaDataErrors.service_level" class="text-red-500 text-xs">
          {{ slaDataErrors.service_level }}
        </span>
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
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-medium">Assignment conditions</span>
        <span class="text-sm text-gray-600">
          Choose which tickets are affected by this policy.
        </span>
      </div>
      <div class="mt-4">
        <Checkbox
          label="Apply default SLA conditions"
          v-model="slaData.default_sla"
        />
        <div class="mt-4" v-if="!slaData.default_sla">
          <SlaAssignmentConditions :conditions="slaData.condition" />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-3">
        <span class="text-lg font-medium">Valid from</span>
        <span class="text-sm text-gray-600">
          Choose how long this SLA policy will be active.
        </span>
      </div>
      <div class="mt-4 flex gap-2">
        <div class="w-full space-y-1.5">
          <label for="from_date" class="text-sm text-gray-600">From date</label>
          <DatePicker
            v-model="slaData.start_date"
            variant="subtle"
            placeholder="From date"
            class="w-full"
            id="from_date"
            @change="debouncedValidateSlaData()"
            :formatter="(date) => getFormat(date)"
          />
          <span v-if="slaDataErrors.start_date" class="text-red-500 text-xs">
            {{ slaDataErrors.start_date }}
          </span>
        </div>
        <div class="w-full space-y-1.5">
          <label for="to_date" class="text-sm text-gray-600">To date</label>
          <DatePicker
            v-model="slaData.end_date"
            variant="subtle"
            placeholder="To date"
            class="w-full"
            id="to_date"
            @change="debouncedValidateSlaData()"
            :formatter="(date) => getFormat(date)"
          />
          <span v-if="slaDataErrors.end_date" class="text-red-500 text-xs">
            {{ slaDataErrors.end_date }}
          </span>
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-medium">Response and resolution</span>
        <span class="text-sm text-gray-600">
          Add time targets around support milestones like first reply and
          resolution times
        </span>
      </div>
      <div class="mt-4">
        <Checkbox
          label="Apply SLA for resolution time"
          v-model="slaData.apply_sla_for_resolution"
        />
        <div class="mt-4">
          <SlaPriorityList
            :priorityList="slaData.priorities"
            :applySlaForResolution="slaData.apply_sla_for_resolution"
          />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-medium">Status details</span>
        <span class="text-sm text-gray-600">
          The SLA status updates with ticket progress—fulfilled when conditions
          are met, paused when awaiting external action.
        </span>
      </div>
      <div class="mt-4">
        <div class="mt-4">
          <SlaStatusList :statusList="slaData.statuses" />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <SlaHolidays
      :workDaysList="slaData.support_and_resolution"
      v-model="slaData.holiday_list"
      :slaData="slaData"
    />
  </div>
</template>

<script setup lang="ts">
import {
  slaActiveScreen,
  slaData,
  slaDataErrors,
  validateSlaData,
} from "./sla";
import {
  createResource,
  Switch,
  Checkbox,
  DatePicker,
  toast,
  Spinner,
} from "frappe-ui";
import { onUnmounted } from "vue";
import SlaPriorityList from "./SlaPriorityList.vue";
import SlaStatusList from "./SlaStatusList.vue";
import SlaHolidays from "./SlaHolidays.vue";
import SlaAssignmentConditions from "./SlaAssignmentConditions.vue";
import { useDebounceFn } from "@vueuse/core";
import { getFormat } from "@/utils";

const debouncedValidateSlaData = useDebounceFn(() => {
  validateSlaData();
}, 300);

const getSlaData = createResource({
  url: "helpdesk.api.sla.get_sla",
  params: {
    docname: slaActiveScreen.value.data?.name,
  },
  onSuccess(data) {
    const fulfilledOn =
      data.sla_fulfilled_on?.map((item) => {
        return {
          ...item,
          sla_behavior: "Fulfilled",
        };
      }) || [];
    const pauseOn =
      data.pause_sla_on?.map((item) => {
        return {
          ...item,
          sla_behavior: "Paused",
        };
      }) || [];

    const conditions = JSON.parse(data.condition || "[]");

    slaData.value = {
      ...data,
      statuses: [...pauseOn, ...fulfilledOn],
      loading: false,
      condition: data.condition?.length > 0 ? conditions : [],
    };
  },
});

if (slaActiveScreen.value.data && slaActiveScreen.value.fetchData) {
  slaData.value.loading = true;
  getSlaData.submit();
}

const goBack = () => {
  slaActiveScreen.value = {
    screen: "list",
    data: null,
    fetchData: true,
  };
};

const saveSla = () => {
  // Reset all errors
  slaDataErrors.value = {
    service_level: "",
    description: "",
    enabled: "",
    default_sla: "",
    apply_sla_for_resolution: "",
    priorities: "",
    statuses: "",
    holiday_list: "",
    default_priority: "",
    start_date: "",
    end_date: "",
    support_and_resolution: "",
    condition: "",
  };

  const validationErrors = validateSlaData();

  if (Object.values(validationErrors).some((error) => error)) {
    toast.error("Please provide all required fields");
    return;
  }

  if (slaActiveScreen.value.data) {
    updateSla();
  } else {
    createSla();
  }
};

const createSla = () => {
  const fulfilledOn = slaData.value.statuses.filter(
    (status) => status.sla_behavior === "Fulfilled"
  );
  const pauseOn = slaData.value.statuses.filter(
    (status) => status.sla_behavior === "Paused"
  );
  createResource({
    url: "helpdesk.api.sla.save_sla",
    params: {
      doc: {
        doctype: "HD Service Level Agreement",
        enabled: slaData.value.enabled,
        description: slaData.value.description,
        service_level: slaData.value.service_level,
        default_sla: slaData.value.default_sla,
        apply_sla_for_resolution: slaData.value.apply_sla_for_resolution,
        priorities: slaData.value.priorities,
        sla_fulfilled_on: fulfilledOn,
        pause_sla_on: pauseOn,
        holiday_list: slaData.value.holiday_list,
        default_priority: slaData.value.default_priority,
        start_date: slaData.value.start_date,
        end_date: slaData.value.end_date,
        support_and_resolution: slaData.value.support_and_resolution,
        condition: slaData.value.condition,
      },
      is_new: true,
    },
    auto: true,
    onSuccess(data) {
      toast.success("SLA policy created successfully");
      slaActiveScreen.value.data = data;
      slaActiveScreen.value.screen = "view";
      getSlaData.submit({
        docname: data.name,
      });
    },
    onError(error) {
      toast.error(`SLA policy creation failed: ${error}`);
    },
  });
};

const updateSla = () => {
  const fulfilledOn = slaData.value.statuses.filter(
    (status) => status.sla_behavior === "Fulfilled"
  );
  const pauseOn = slaData.value.statuses.filter(
    (status) => status.sla_behavior === "Paused"
  );
  createResource({
    url: "helpdesk.api.sla.save_sla",
    params: {
      doc: {
        doctype: "HD Service Level Agreement",
        name: slaActiveScreen.value.data.name,
        enabled: slaData.value.enabled,
        description: slaData.value.description,
        service_level: slaData.value.service_level,
        default_sla: slaData.value.default_sla,
        apply_sla_for_resolution: slaData.value.apply_sla_for_resolution,
        priorities: slaData.value.priorities,
        sla_fulfilled_on: fulfilledOn,
        pause_sla_on: pauseOn,
        holiday_list: slaData.value.holiday_list,
        default_priority: slaData.value.default_priority,
        start_date: slaData.value.start_date,
        end_date: slaData.value.end_date,
        support_and_resolution: slaData.value.support_and_resolution,
        condition: slaData.value.condition,
      },
      is_new: false,
    },
    auto: true,
    onSuccess() {
      getSlaData.submit();
      toast.success("SLA policy updated successfully");
    },
    onError(error) {
      toast.error(`SLA policy update failed: ${error}`);
    },
  });
};

onUnmounted(() => {
  slaDataErrors.value = {
    service_level: "",
    description: "",
    enabled: "",
    default_sla: "",
    apply_sla_for_resolution: "",
    priorities: "",
    statuses: "",
    holiday_list: "",
    default_priority: "",
    start_date: "",
    end_date: "",
    support_and_resolution: "",
    condition: "",
  };
});
</script>
