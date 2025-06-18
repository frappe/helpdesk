<template>
  <div v-if="!holidayData.loading" class="pb-12">
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
            {{ holidayData.holiday_list_name || "New Holiday List" }}
          </h1>
        </div>
      </div>
      <Button
        label="Save"
        theme="gray"
        variant="solid"
        @click="saveHoliday()"
      />
    </div>
    <div class="flex items-center justify-between gap-2 mt-8">
      <span class="text-sm"> Total holidays (Calculated automatically) </span>
      <Input size="sm" variant="subtle" value="123" disabled />
    </div>
    <hr class="mb-6 mt-3" />
    <div class="grid grid-cols-2 gap-2">
      <FormControl
        :type="'text'"
        size="sm"
        variant="subtle"
        placeholder="Name"
        label="Name"
        v-model="holidayData.holiday_list_name"
        required
      />
      <FormControl
        :type="'textarea'"
        size="sm"
        variant="subtle"
        placeholder="Description"
        label="Description"
        v-model="holidayData.description"
        required
      />
    </div>
    <hr class="my-6" />
    <div class="flex justify-between items-center">
      <div class="flex flex-col gap-2">
        <span class="text-lg font-medium">Associate holiday list</span>
        <span class="text-sm text-gray-600">
          Link a holiday list to skip business hours on specified dates.
        </span>
      </div>
      <Switch />
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-medium">Weekly schedule set up</span>
        <span class="text-sm text-gray-600">
          Define your team’s weekly working days, off days, and operating hours
          in one place
        </span>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-medium">Holidays</span>
        <span class="text-sm text-gray-600">
          Add holidays here to make sure they’re excluded from SLA calculations.
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { activeScreen } from "./holidaylist";
import { createResource, Input, Switch } from "frappe-ui";
import { ref } from "vue";

const holidayData = ref({
  holiday_list_name: "",
  description: "",
  loading: false,
});

if (activeScreen.value.data) {
  holidayData.value.loading = true;
  createResource({
    url: "helpdesk.api.holiday_list.get_holiday_list",
    params: {
      docname: activeScreen.value.data.name,
    },
    auto: true,
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
      holidayData.value = {
        ...data,
        statuses: [...pauseOn, ...fulfilledOn],
        loading: false,
      };
    },
  });
}

const goBack = () => {
  activeScreen.value = {
    screen: "list",
    data: null,
  };
};

const saveHoliday = () => {
  if (activeScreen.value.data) {
    updateHoliday();
  } else {
    createHoliday();
  }
};

const createHoliday = () => {
  //   createResource({
  //     url: "frappe.client.insert",
  //     params: {
  //       doc: {
  //         doctype: "HD Service Level Agreement",
  //         enabled: slaData.value.enabled,
  //         description: slaData.value.description,
  //         service_level: slaData.value.service_level,
  //         default_sla: slaData.value.default_sla,
  //         apply_sla_for_resolution: slaData.value.apply_sla_for_resolution,
  //         priorities: slaData.value.priorities,
  //         sla_fulfilled_on: fulfilledOn,
  //         pause_sla_on: pauseOn,
  //         holiday_list: slaData.value.holiday_list,
  //         default_priority: slaData.value.default_priority,
  //         start_date: slaData.value.start_date,
  //         end_date: slaData.value.end_date,
  //       },
  //     },
  //     auto: true,
  //     onSuccess(data) {
  //       console.log("data", data);
  //     },
  //   });
};

const updateHoliday = () => {
  //   createResource({
  //     url: "frappe.client.set_value",
  //     params: {
  //       doctype: "HD Service Level Agreement",
  //       name: activeScreen.value.data.name,
  //       fieldname: {
  //         enabled: slaData.value.enabled,
  //         description: slaData.value.description,
  //         service_level: slaData.value.service_level,
  //         default_sla: slaData.value.default_sla,
  //         apply_sla_for_resolution: slaData.value.apply_sla_for_resolution,
  //         priorities: slaData.value.priorities,
  //         sla_fulfilled_on: fulfilledOn,
  //         pause_sla_on: pauseOn,
  //         holiday_list: slaData.value.holiday_list,
  //         default_priority: slaData.value.default_priority,
  //         start_date: slaData.value.start_date,
  //         end_date: slaData.value.end_date,
  //       },
  //     },
  //     auto: true,
  //     onSuccess(data) {
  //       console.log("data", data);
  //     },
  //   });
};
</script>
