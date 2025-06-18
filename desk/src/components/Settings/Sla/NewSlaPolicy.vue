<template>
  <div class="pb-8">
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
      <Button label="Save" theme="gray" variant="solid" @click="savePolicy()" />
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
      <!-- ###@@@@### TODO: handle save for default priority ####@@@@@#### -->
      <FormControl
        type="select"
        :options="priorityOptions"
        size="sm"
        variant="subtle"
        label="Default Priority"
        v-model="slaData.default_priority"
      />
      <FormControl
        :type="'textarea'"
        size="sm"
        variant="subtle"
        placeholder="Description"
        label="Description"
        v-model="slaData.description"
        required
      />
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-semibold">Assignment conditions</span>
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
          <SlaAssignmentConditions />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-semibold">Valid from</span>
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
        <span class="text-lg font-semibold">Response and resolution</span>
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
          <SlaPriorityList :priorityListData="priorityOptions" />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-semibold">Status details</span>
        <span class="text-sm text-gray-600">
          The SLA status updates with ticket progress—fulfilled when conditions
          are met, paused when awaiting external action.
        </span>
      </div>
      <div class="mt-4">
        <div class="mt-4">
          <SlaStatusList />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div class="flex flex-col gap-2">
      <div class="text-lg font-semibold">Work Schedule & Holidays</div>
      <div>
        <div class="text-sm text-gray-600">
          Set working days, hours, and holidays by selecting a predefined
          schedule or creating a new one.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Button,
  Badge,
  createResource,
  Switch,
  Checkbox,
  toast,
} from "frappe-ui";
import { activeScreen } from "./sla";
import { computed, ref } from "vue";
import SlaAssignmentConditions from "./SlaAssignmentConditionsOld.vue";
import SlaPriorityList from "./SlaPriorityList.vue";
import SlaStatusList from "./SlaStatusList.vue";

const holidayList = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "HD Service Holiday List",
    fields: ["*"],
    parent: "HD Service Level Agreement",
  },
  auto: true,
  onSuccess: (data) => {
    console.log("holidayList", data);
  },
});

const slaData = ref({
  service_level: "",
  default_priority: "",
  description: "",
  default_sla: false,
  enabled: false,
  apply_sla_for_resolution: false,
  start_date: "",
  end_date: "",
});

const selectedOption = ref("2");

const priorityOptions = ref([]);

const goBack = () => {
  activeScreen.value = {
    screen: "list",
    data: null,
  };
};

const savePolicy = () => {
  createResource({
    url: "frappe.client.insert",
    method: "POST",
    params: {
      doc: {
        doctype: "HD Service Level Agreement",
        enabled: 1,
        default_sla: 0,
        apply_sla_for_resolution: 1,
        priorities: [
          {
            docstatus: 0,
            doctype: "HD Service Level Priority",
            name: "new-hd-service-level-priority-mvaiqxemmo",
            __islocal: 1,
            __unsaved: 1,
            owner: "Administrator",
            default_priority: 1,
            parent: "new-hd-service-level-agreement-alojvfcbpf",
            parentfield: "priorities",
            parenttype: "HD Service Level Agreement",
            idx: 1,
            priority: "High",
            response_time: 3600,
            resolution_time: 3600,
          },
        ],
        sla_fulfilled_on: [
          {
            docstatus: 0,
            doctype: "HD Service Level Agreement Fulfilled On Status",
            name: "new-hd-service-level-agreement-fulfilled-on-status-iqyljidbki",
            __islocal: 1,
            __unsaved: 1,
            owner: "Administrator",
            status: "Open",
            parent: "new-hd-service-level-agreement-alojvfcbpf",
            parentfield: "sla_fulfilled_on",
            parenttype: "HD Service Level Agreement",
            idx: 1,
          },
        ],
        pause_sla_on: [
          {
            docstatus: 0,
            doctype: "HD Pause Service Level Agreement On Status",
            name: "new-hd-pause-service-level-agreement-on-status-ioektrmknt",
            __islocal: 1,
            __unsaved: 1,
            owner: "Administrator",
            status: "Replied",
            parent: "new-hd-service-level-agreement-alojvfcbpf",
            parentfield: "pause_sla_on",
            parenttype: "HD Service Level Agreement",
            idx: 1,
            __unedited: false,
          },
        ],
        support_and_resolution: [
          {
            docstatus: 0,
            doctype: "HD Service Day",
            name: "new-hd-service-day-jflzuiwhhb",
            __islocal: 1,
            __unsaved: 1,
            owner: "Administrator",
            workday: "Monday",
            parent: "new-hd-service-level-agreement-alojvfcbpf",
            parentfield: "support_and_resolution",
            parenttype: "HD Service Level Agreement",
            idx: 1,
            start_time: "07:46:53",
            end_time: "16:46:55",
          },
        ],
        service_level: "test api",
        description: "svdv",
        holiday_list: "Default",
      },
    },
    auto: true,
    onSuccess: () => {
      toast.success("Policy saved successfully");
    },
    onError: () => {
      toast.error("Policy saved failed");
    },
  });
};
// const savePolicy = () => {
//   createResource({
//     url: "frappe.client.insert",
//     method: "POST",
//     params: {
//       doc: {
//         doctype: "HD Service Level Agreement",
//         service_level: slaData.value.service_level,
//         default_priority: slaData.value.default_priority,
//         description: slaData.value.description,
//         enabled: slaData.value.enabled,
//         default_sla: slaData.value.default_sla,
//         apply_sla_for_resolution: slaData.value.apply_sla_for_resolution,
//         start_date: slaData.value.start_date,
//         end_date: slaData.value.end_date,
//       },
//     },
//     auto: true,
//     onSuccess: () => {
//       toast.success("Policy saved successfully");
//     },
//     onError: () => {
//       toast.error("Policy saved failed");
//     },
//   });
// };
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

label {
  cursor: pointer;
  user-select: none;
}
</style>
