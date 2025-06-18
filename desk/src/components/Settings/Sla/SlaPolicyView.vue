<template>
  <div v-if="!slaData.loading" class="pb-12">
    <div class="flex items-center justify-between">
      <div>
        <div class="flex items-center gap-2">
          <Button
            @click="goBack()"
            theme="gray"
            variant="ghost"
            icon="chevron-left"
            size="sm"
            class="-ml-2"
          />
          <h1 class="text-lg font-semibold">
            {{ slaData.service_level || "New SLA Policy" }}
          </h1>
          <Badge
            :variant="'subtle'"
            theme="blue"
            size="sm"
            :label="slaData.enabled ? 'Enabled' : 'Disabled'"
          />
        </div>
      </div>
      <Button label="Save" theme="gray" variant="solid" @click="saveSla()" />
    </div>
    <div class="flex items-center justify-between gap-2 mt-8">
      <span class="text-sm"> Enable Policy </span>
      <Switch size="sm" v-model="slaData.enabled" />
    </div>
    <hr class="mb-6 mt-3" />
    <div class="grid grid-cols-2 gap-2">
      <FormControl
        :type="'text'"
        size="sm"
        variant="subtle"
        placeholder="Name"
        label="Name"
        v-model="slaData.service_level"
        required
      />
      <FormControl
        :type="'textarea'"
        size="sm"
        variant="subtle"
        placeholder="Description"
        label="Description"
        v-model="slaData.description"
        required
        :rows="1"
      />
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-medium">Assignment conditions</span>
        <span class="text-sm text-gray-600">
          Choose which tickets are affected by this policy. Learn about
          conditions
        </span>
      </div>
      <div class="mt-4">
        <Checkbox
          label="Apply default SLA conditions"
          v-model="slaData.default_sla"
        />
        <div class="mt-4">
          <SlaAssignmentConditions :conditions="slaData.condition" />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-medium">Valid from</span>
        <span class="text-sm text-gray-600">
          Choose how long this SLA policy will be active.
        </span>
      </div>
      <div class="mt-4 flex gap-2">
        <FormControl
          :type="'date'"
          size="sm"
          variant="subtle"
          placeholder="From date"
          label="From date"
          v-model="slaData.start_date"
          class="w-full"
        />
        <FormControl
          :type="'date'"
          size="sm"
          variant="subtle"
          placeholder="To date"
          label="To date"
          v-model="slaData.end_date"
          class="w-full"
        />
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
          <SlaPriorityList :priorityList="slaData.priorities" />
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
    />
  </div>
</template>

<script setup lang="ts">
import { activeScreen } from "./sla";
import { createResource, Switch, Checkbox } from "frappe-ui";
import { ref } from "vue";
import SlaPriorityList from "./SlaPriorityList.vue";
import SlaStatusList from "./SlaStatusList.vue";
import SlaHolidays from "./SlaHolidays.vue";
import SlaAssignmentConditions from "./SlaAssignmentConditions.vue";

const defaultWorkDays = [
  {
    workday: "Monday",
    start_time: "09:00",
    end_time: "17:00",
    is_holiday: false,
  },
  {
    workday: "Tuesday",
    start_time: "09:00",
    end_time: "17:00",
    is_holiday: false,
  },
  {
    workday: "Wednesday",
    start_time: "09:00",
    end_time: "17:00",
    is_holiday: false,
  },
  {
    workday: "Thursday",
    start_time: "09:00",
    end_time: "17:00",
    is_holiday: false,
  },
  {
    workday: "Friday",
    start_time: "09:00",
    end_time: "17:00",
    is_holiday: false,
  },
  {
    workday: "Saturday",
    start_time: "09:00",
    end_time: "17:00",
    is_holiday: false,
  },
  {
    workday: "Sunday",
    start_time: "09:00",
    end_time: "17:00",
    is_holiday: false,
  },
];

const slaData = ref({
  service_level: "",
  description: "",
  enabled: false,
  default_sla: false,
  apply_sla_for_resolution: false,
  priorities: [],
  statuses: [],
  holiday_list: "Default",
  default_priority: "",
  start_date: "",
  end_date: "",
  loading: false,
  support_and_resolution: defaultWorkDays,
  condition: [],
});

const getSlaData = createResource({
  url: "helpdesk.api.sla.get_sla",
  params: {
    docname: activeScreen.value.data?.name,
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

    const workDays = data.support_and_resolution || [];
    const existingDays = workDays.map((day) => day.workday);
    let missingDays =
      defaultWorkDays.filter((day) => !existingDays.includes(day.workday)) ||
      [];

    missingDays = missingDays.map((day) => ({
      ...day,
      is_holiday: true,
    }));

    const conditions = JSON.parse(data.condition || "[]");

    slaData.value = {
      ...data,
      statuses: [...pauseOn, ...fulfilledOn],
      loading: false,
      support_and_resolution: [...workDays, ...missingDays],
      condition: data.condition?.length > 0 ? conditions : [],
    };
  },
});

if (activeScreen.value.data) {
  slaData.value.loading = true;
  getSlaData.submit();
}

const goBack = () => {
  activeScreen.value = {
    screen: "list",
    data: null,
  };
};

const saveSla = () => {
  if (activeScreen.value.data) {
    updateSla();
  } else {
    createSla();
  }
};

const tempCreateSla = () => {
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
        name: activeScreen.value.data.name,
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
    onSuccess(data) {
      getSlaData.submit();
    },
  });
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
      console.log("data", data);
      getSlaData.submit();
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
  console.log("@@@@@@@@@@@@@@@@@", slaData.value);
  createResource({
    url: "helpdesk.api.sla.save_sla",
    params: {
      doc: {
        doctype: "HD Service Level Agreement",
        name: activeScreen.value.data.name,
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
    onSuccess(data) {
      console.log("data", data);
      getSlaData.submit();
    },
  });
};
</script>
