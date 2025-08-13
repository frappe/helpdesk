<template>
  <Dialog v-model="show" :options="dialogOptions" @after-leave="resetCallLog">
    <template #body>
      <div class="px-4 pt-5 bg-surface-modal sm:px-6">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-2">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __(dialogOptions.title) || __("Untitled") }}
            </h3>
            <Badge v-if="isDirty" :label="'Not Saved'" theme="orange" />
          </div>
          <div class="flex items-center gap-1">
            <Button variant="ghost" class="w-7" @click="show = false">
              <template #icon>
                <FeatherIcon name="x" class="size-4" />
              </template>
            </Button>
          </div>
        </div>
        <div class="flex flex-col gap-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <FormLabel label="Type" required />
              <Select
                v-model="callLog.type"
                :options="callLogTypeOptions"
                placeholder="Type"
              />
              <ErrorMessage :message="errors.type" />
            </div>
            <div class="flex flex-col gap-1.5">
              <FormLabel label="To" required />
              <FormControl v-model="callLog.to" type="text" placeholder="To" />
              <ErrorMessage :message="errors.to" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <FormLabel label="From" required />
              <FormControl
                v-model="callLog.from"
                type="text"
                placeholder="From"
              />
              <ErrorMessage :message="errors.from" />
            </div>
            <div class="flex flex-col gap-1.5">
              <FormLabel label="Status" required />
              <Select
                v-model="callLog.status"
                :options="callLogStatusOptions"
                placeholder="Status"
              ></Select>
              <ErrorMessage :message="errors.status" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <FormLabel label="Duration" required />
              <FormControl
                v-model="callLog.duration"
                type="number"
                placeholder="Duration"
                description="Call duration in seconds"
              />
              <ErrorMessage :message="errors.duration" />
            </div>
            <div
              class="flex flex-col gap-1.5"
              v-if="callLog.type === 'Incoming'"
            >
              <FormLabel label="Call Received By" :required="editMode" />
              <Link
                :value="callLog.receiver"
                :doctype="'User'"
                :placeholder="'Call Received By'"
                @change="(data) => (callLog.receiver = data)"
              />
            </div>
            <div
              class="flex flex-col gap-1.5"
              v-if="callLog.type === 'Outgoing'"
            >
              <FormLabel label="Caller" :required="editMode" />
              <Link
                :value="callLog.caller"
                :doctype="'User'"
                :placeholder="'Caller'"
                @change="(data) => (callLog.caller = data)"
              />
            </div>
          </div>
        </div>
      </div>
      <div class="px-4 pt-4 pb-7 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            v-for="action in dialogOptions.actions"
            :key="action.label"
            v-bind="action"
            :label="__(action.label)"
            :loading="loading"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { getRandom } from "@/utils";
import {
  createResource,
  Dialog,
  ErrorMessage,
  FormControl,
  FormLabel,
  Select,
  toast,
  type DialogProps,
} from "frappe-ui";
import { computed, ref, watch } from "vue";

const show = defineModel<boolean>();
const editMode = ref(false);
const loading = ref(false);
const isDirty = ref(false);
const originalCallLog = ref("");
const emit = defineEmits(["afterInsert"]);

const errors = ref({
  type: "",
  to: "",
  from: "",
  status: "",
  duration: "",
});

const callLog = ref({
  receiver: "",
  caller: "",
  type: "",
  to: "",
  from: "",
  status: "",
  duration: 0,
});

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
});

const callLogTypeOptions = [
  { label: "", value: "" },
  { label: "Incoming", value: "Incoming" },
  { label: "Outgoing", value: "Outgoing" },
];

const callLogStatusOptions = [
  { label: "", value: "" },
  { label: "Completed", value: "Completed" },
  { label: "Busy", value: "Busy" },
  { label: "Failed", value: "Failed" },
  { label: "Initiated", value: "Initiated" },
  { label: "Queued", value: "Queued" },
  { label: "Canceled", value: "Canceled" },
  { label: "Ringing", value: "Ringing" },
  { label: "No Answer", value: "No Answer" },
  { label: "In Progress", value: "In Progress" },
];

const dialogOptions = computed<DialogProps["options"]>(() => ({
  title: !editMode.value ? "New Call Log" : "Edit Call Log",
  size: "xl",
  actions: [
    {
      label: editMode.value ? "Save" : "Create",
      variant: "solid",
      onClick: () => {
        if (editMode.value) {
          updateCallLog();
        } else {
          createCallLog();
        }
      },
      disabled: !isDirty.value,
    },
  ],
}));

const resetCallLog = () => {
  callLog.value = {
    receiver: "",
    caller: "",
    type: "",
    to: "",
    from: "",
    status: "",
    duration: 0,
  };
  originalCallLog.value = JSON.stringify(callLog.value);
  errors.value = {
    type: "",
    to: "",
    from: "",
    status: "",
    duration: "",
  };
  loading.value = false;
};

function updateCallLog() {
  validateCallLog();
  if (Object.values(errors.value).some((error) => error)) {
    toast.error("Please fill all required fields");
    return;
  }
  loading.value = true;
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "TF Call Log",
      name: props.data.name,
      fieldname: {
        ...callLog.value,
      },
    },
    auto: true,
    onSuccess(doc) {
      loading.value = false;
      handleCallLogUpdate(doc);
    },
  });
}

function createCallLog() {
  validateCallLog();
  if (Object.values(errors.value).some((error) => error)) {
    toast.error("Please fill all required fields");
    return;
  }
  loading.value = true;
  createResource({
    url: "frappe.client.insert",
    params: {
      doc: {
        doctype: "TF Call Log",
        ...callLog.value,
        id: getRandom(12),
        telephony_medium: "Manual",
      },
    },
    auto: true,
    onSuccess(doc) {
      loading.value = false;
      handleCallLogUpdate(doc);
    },
  });
}

function handleCallLogUpdate(doc) {
  show.value = false;
  emit("afterInsert", doc);
}

const validateCallLog = () => {
  if (!callLog.value.type) {
    errors.value.type = "Type is required";
  } else {
    errors.value.type = "";
  }

  if (!callLog.value.to) {
    errors.value.to = "To is required";
  } else if (!/^[\d\+\-\(\)\s]{5,20}$/.test(callLog.value.to)) {
    errors.value.to = "Please enter a valid phone number";
  } else {
    errors.value.to = "";
  }

  if (!callLog.value.from) {
    errors.value.from = "From is required";
  } else if (!/^[\d\+\-\(\)\s]{5,20}$/.test(callLog.value.from)) {
    errors.value.from = "Please enter a valid phone number";
  } else {
    errors.value.from = "";
  }

  if (!callLog.value.status) {
    errors.value.status = "Status is required";
  } else {
    errors.value.status = "";
  }

  if (!callLog.value.duration) {
    errors.value.duration = "Duration is required";
  } else {
    errors.value.duration = "";
  }
};

watch(
  callLog,
  (newValue) => {
    isDirty.value = JSON.stringify(newValue) !== originalCallLog.value;
  },
  { deep: true }
);

watch(
  () => props.data,
  (newValue) => {
    editMode.value = newValue?.name ? true : false;

    if (newValue?.name) {
      callLog.value = {
        receiver: newValue.receiver,
        caller: newValue.caller,
        type: newValue.type,
        to: newValue.to,
        from: newValue.from,
        status: newValue.status,
        duration: newValue.duration,
      };
    }
    originalCallLog.value = JSON.stringify(callLog.value);
  },
  { deep: true }
);
</script>
