<template>
  <div v-if="slaData.loading" class="flex items-center h-full justify-center">
    <LoadingIndicator class="w-4" />
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
            class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-xl hover:opacity-70"
          />
          <Badge
            :variant="'subtle'"
            :theme="slaData.enabled ? 'blue' : 'gray'"
            size="sm"
            :label="slaData.enabled ? 'Enabled' : 'Disabled'"
          />
        </div>
      </div>
      <div class="flex gap-2 items-center">
        <Badge
          :variant="'subtle'"
          :theme="'orange'"
          size="sm"
          label="Unsaved changes"
          v-if="isDirty"
        />
        <Button
          label="Save"
          theme="gray"
          variant="solid"
          @click="saveSla()"
          :disabled="Boolean(!isDirty && slaActiveScreen.data)"
        />
      </div>
    </div>
  </div>
  <div v-if="!slaData.loading" class="overflow-y-auto px-10 pb-10">
    <div class="flex items-center justify-between gap-2" @click="toggleEnabled">
      <span class="text-sm text-ink-gray-7">Enable Policy</span>
      <Switch size="sm" :model-value="slaData.enabled" />
    </div>
    <hr class="mb-6 mt-3" />
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
          :disabled="slaActiveScreen.data"
        />
        <ErrorMessage :message="slaDataErrors.service_level" />
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
        <span class="text-lg font-semibold text-ink-gray-7"
          >Assignment conditions</span
        >
        <span class="text-sm text-ink-gray-6">
          Choose which tickets are affected by this policy.
        </span>
      </div>
      <div class="mt-4">
        <Checkbox
          label="Set as default SLA"
          :model-value="slaData.default_sla"
          @update:model-value="toggleDefaultSla"
          class="text-ink-gray-6 text-base font-medium"
        />
        <div class="mt-4" v-if="!slaData.default_sla">
          <SlaAssignmentConditions :conditions="slaData.condition_json" />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-3">
        <span class="text-lg font-semibold text-ink-gray-7">Valid from</span>
        <span class="text-sm text-ink-gray-6">
          Choose how long this SLA policy will be active.
        </span>
      </div>
      <div class="mt-4 flex gap-5 flex-col md:flex-row">
        <div class="w-full space-y-1.5">
          <label for="from_date" class="text-sm text-gray-600">From date</label>
          <DatePicker
            v-model="slaData.start_date"
            variant="subtle"
            placeholder="From date"
            class="w-full"
            id="from_date"
            @change="validateSlaData('start_date')"
            :formatter="(date) => getFormattedDate(date)"
          />
          <ErrorMessage :message="slaDataErrors.start_date" />
        </div>
        <div class="w-full space-y-1.5">
          <label for="to_date" class="text-sm text-gray-600">To date</label>
          <DatePicker
            v-model="slaData.end_date"
            variant="subtle"
            placeholder="To date"
            class="w-full"
            id="to_date"
            @change="validateSlaData('end_date')"
            :formatter="(date) => getFormattedDate(date)"
          />
          <ErrorMessage :message="slaDataErrors.end_date" />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-semibold text-ink-gray-7"
          >Response and resolution</span
        >
        <span class="text-sm text-ink-gray-6">
          Add time targets around support milestones like first reply and
          resolution times
        </span>
      </div>
      <div class="mt-4">
        <Checkbox
          label="Apply SLA for resolution time also"
          v-model="slaData.apply_sla_for_resolution"
          class="text-ink-gray-6 text-base font-medium"
          @change="validateSlaData('priorities')"
        />
        <div class="mt-4">
          <SlaPriorityList />
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-semibold text-ink-gray-7"
          >Status details</span
        >
        <span class="text-sm text-ink-gray-6">
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
    <SlaHolidays />
  </div>
  <ConfirmDialog
    v-model="showConfirmDialog"
    title="Unsaved changes"
    message="Are you sure you want to go back? Unsaved changes will be lost."
    :onConfirm="goBack"
    :onCancel="() => (showConfirmDialog = false)"
  />
</template>

<script setup lang="ts">
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import {
  resetSlaDataErrors,
  slaActiveScreen,
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
  LoadingIndicator,
  Switch,
  toast,
} from "frappe-ui";
import { onMounted, onUnmounted, ref, watch } from "vue";
import SlaAssignmentConditions from "./SlaAssignmentConditions.vue";
import SlaHolidays from "./SlaHolidays.vue";
import SlaPriorityList from "./SlaPriorityList.vue";
import SlaStatusList from "./SlaStatusList.vue";

const showConfirmDialog = ref(false);
const isDirty = ref(false);
const initialData = ref(null);

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

    const condition_json = JSON.parse(data.condition_json || "[]");

    const newData = {
      ...data,
      statuses: [...pauseOn, ...fulfilledOn],
      loading: false,
      condition_json: condition_json,
    };
    slaData.value = newData;
    initialData.value = JSON.stringify(newData);
  },
});

if (slaActiveScreen.value.data && slaActiveScreen.value.fetchData) {
  slaData.value.loading = true;
  getSlaData.submit();
}

const goBack = () => {
  if (isDirty.value && !showConfirmDialog.value) {
    showConfirmDialog.value = true;
    return;
  }
  if (!slaActiveScreen.value.data && !showConfirmDialog.value) {
    showConfirmDialog.value = true;
    return;
  }
  slaActiveScreen.value = {
    screen: "list",
    data: null,
    fetchData: true,
  };
};

const saveSla = () => {
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
    url: "frappe.client.insert",
    params: {
      doc: {
        ...slaData.value,
        doctype: "HD Service Level Agreement",
        sla_fulfilled_on: fulfilledOn,
        pause_sla_on: pauseOn,
        condition: convertToConditions({
          conditions: slaData.value.condition_json,
          fieldPrefix: "doc",
        }),
        condition_json: JSON.stringify(slaData.value.condition_json),
      },
    },
    auto: true,
    onSuccess(data) {
      toast.success("SLA policy created");
      slaActiveScreen.value.data = data;
      slaActiveScreen.value.screen = "view";
      getSlaData.submit({
        docname: data.name,
      });
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
    url: "frappe.client.set_value",
    params: {
      doctype: "HD Service Level Agreement",
      name: slaActiveScreen.value.data.name,
      fieldname: {
        ...slaData.value,
        name: slaActiveScreen.value.data.name,
        sla_fulfilled_on: fulfilledOn,
        pause_sla_on: pauseOn,
        condition: convertToConditions({
          conditions: slaData.value.condition_json,
          fieldPrefix: "doc",
        }),
        condition_json: JSON.stringify(slaData.value.condition_json),
      },
    },
    auto: true,
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

watch(
  slaData,
  (newVal) => {
    if (!initialData.value) return;
    isDirty.value = JSON.stringify(newVal) != initialData.value;
  },
  { deep: true }
);

const beforeUnloadHandler = (event) => {
  if (!isDirty.value) return;
  event.preventDefault();
  event.returnValue = true;
};

onMounted(() => {
  addEventListener("beforeunload", beforeUnloadHandler);
});

onUnmounted(() => {
  removeEventListener("beforeunload", beforeUnloadHandler);
  resetSlaDataErrors();
});
</script>
