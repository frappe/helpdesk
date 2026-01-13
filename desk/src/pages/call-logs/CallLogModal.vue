<template>
  <Dialog v-model="show" :options="dialogOptions" @after-leave="resetCallLog">
    <template #body>
      <div class="px-4 pt-5 bg-surface-modal sm:px-6">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-2">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __(dialogOptions.title) || __("Untitled") }}
            </h3>
            <Badge v-if="isDirty" :label="__('Not Saved')" theme="orange" />
          </div>
          <div class="flex items-center gap-1">
            <Button
              variant="ghost"
              class="w-7"
              @click="show = false"
              icon="x"
            />
          </div>
        </div>
        <div class="flex flex-col gap-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <FormLabel :label="__('Type')" required />
              <Select
                v-model="callLog.type"
                :options="callLogTypeOptions"
                :placeholder="__('Select')"
              />
              <ErrorMessage :message="errors.type" />
            </div>
            <div class="flex flex-col gap-1.5">
              <FormLabel :label="__('To')" required />
              <FormControl
                v-model="callLog.to"
                type="text"
                :placeholder="__('+18596748596')"
              />
              <ErrorMessage :message="errors.to" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <FormLabel :label="__('From')" required />
              <FormControl
                v-model="callLog.from"
                type="text"
                :placeholder="__('+19138276548')"
              />
              <ErrorMessage :message="errors.from" />
            </div>
            <div class="flex flex-col gap-1.5">
              <FormLabel :label="__('Status')" required />
              <Select
                v-model="callLog.status"
                :options="callLogStatusOptions"
                :placeholder="__('Select')"
              ></Select>
              <ErrorMessage :message="errors.status" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-1.5">
              <FormLabel :label="__('Duration')" required />
              <FormControl
                v-model="callLog.duration"
                type="number"
                :placeholder="__('Duration')"
                :description="__('Call duration in seconds')"
              />
              <ErrorMessage :message="errors.duration" />
            </div>
            <div
              class="flex flex-col gap-1.5"
              v-if="callLog.type === 'Incoming'"
            >
              <Link
                :value="callLog.receiver"
                :doctype="'User'"
                :placeholder="__('Select')"
                :label="__('Call Received By')"
                @change="(data) => (callLog.receiver = data)"
              />
            </div>
            <div
              class="flex flex-col gap-1.5"
              v-if="callLog.type === 'Outgoing'"
            >
              <Link
                :value="callLog.caller"
                :doctype="'User'"
                :placeholder="__('Select')"
                :label="__('Caller')"
                @change="(data) => (callLog.caller = data)"
              />
            </div>
            <div class="flex flex-col gap-1.5">
              <Link
                :value="callLog.ticket"
                :doctype="'HD Ticket'"
                :placeholder="__('Select')"
                :label="__('Ticket')"
                :show-description="true"
                @change="(data) => (callLog.ticket = String(data))"
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
import { useAuthStore } from "@/stores/auth";
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
import { __ } from "@/translation";

const show = defineModel<boolean>();
const editMode = ref(false);
const loading = ref(false);
const isDirty = ref(false);
const originalCallLog = ref("");
const emit = defineEmits(["afterInsert"]);
const { user } = useAuthStore();

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
  ticket: "",
});

const props = defineProps({
  callLogId: {
    type: String,
    default: "",
  },
  ticketId: {
    type: String,
    default: "",
  },
});

const callLogData = createResource({
  url: "telephony.api.get_call_log",
  onSuccess(data) {
    const linkedTicket = data.links.find(
      (link) => link.link_doctype == "HD Ticket"
    );
    callLog.value = {
      receiver: data.receiver,
      caller: data.caller,
      type: data.type,
      to: data.to,
      from: data.from,
      status: data.status,
      duration: data.duration || 0,
      ticket: String(linkedTicket?.link_name || ""),
    };
    originalCallLog.value = JSON.stringify(callLog.value);
  },
  auto: false,
});

const callLogTypeOptions = [
  { label: "", value: "" },
  { label: __("Incoming"), value: "Incoming" },
  { label: __("Outgoing"), value: "Outgoing" },
];

const callLogStatusOptions = [
  { label: "", value: "" },
  { label: __("Completed"), value: "Completed" },
  { label: __("Busy"), value: "Busy" },
  { label: __("Failed"), value: "Failed" },
  { label: __("Initiated"), value: "Initiated" },
  { label: __("Queued"), value: "Queued" },
  { label: __("Canceled"), value: "Canceled" },
  { label: __("Ringing"), value: "Ringing" },
  { label: __("No Answer"), value: "No Answer" },
  { label: __("In Progress"), value: "In Progress" },
];

const dialogOptions = computed<DialogProps["options"]>(() => ({
  title: !editMode.value ? __("New Call Log") : __("Edit Call Log"),
  size: "xl",
  actions: [
    {
      label: editMode.value ? __("Save") : __("Create"),
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
    ticket: "",
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
    toast.error(__("Please fill all required fields"));
    return;
  }
  loading.value = true;
  const links = [];
  if (callLog.value.ticket) {
    links.push({
      link_doctype: "HD Ticket",
      link_name: callLog.value.ticket,
    });
  }
  // Copy old links
  callLogData.data.links.forEach((link) => {
    if (link.link_doctype == "HD Ticket") {
      return;
    }
    links.push(link);
  });

  if (callLog.value.receiver == "@me") {
    callLog.value.receiver = user;
  }
  if (callLog.value.caller == "@me") {
    callLog.value.caller = user;
  }
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "TP Call Log",
      name: props.callLogId,
      fieldname: {
        ...callLog.value,
        links,
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
    toast.error(__("Please fill all required fields"));
    return;
  }
  loading.value = true;
  const links = [];
  if (callLog.value.ticket) {
    links.push({
      link_doctype: "HD Ticket",
      link_name: callLog.value.ticket,
    });
  }
  if (callLog.value.receiver == "@me") {
    callLog.value.receiver = user;
  }
  if (callLog.value.caller == "@me") {
    callLog.value.caller = user;
  }
  createResource({
    url: "telephony.api.create_call_log",
    params: {
      id: getRandom(12),
      telephony_medium: "Manual",
      from_number: callLog.value.from,
      to_number: callLog.value.to,
      duration: callLog.value.duration,
      status: callLog.value.status,
      call_type: callLog.value.type,
      caller: callLog.value.caller,
      receiver: callLog.value.receiver,
      ticket: callLog.value.ticket,
      links,
    },
    auto: true,
    onSuccess(doc) {
      loading.value = false;
      handleCallLogUpdate(doc);
    },
    onError() {
      loading.value = false;
    },
  });
}

function handleCallLogUpdate(doc) {
  show.value = false;
  emit("afterInsert", doc);
}

const validateCallLog = () => {
  if (!callLog.value.type) {
    errors.value.type = __("Type is required");
  } else {
    errors.value.type = "";
  }

  if (!callLog.value.to) {
    errors.value.to = __("To is required");
  } else if (!/^\+?\d{8,15}$/.test(callLog.value.to)) {
    errors.value.to = __("Please enter a valid phone number");
  } else {
    errors.value.to = "";
  }

  if (!callLog.value.from) {
    errors.value.from = __("From is required");
  } else if (!/^\+?\d{8,15}$/.test(callLog.value.from)) {
    errors.value.from = __("Please enter a valid phone number");
  } else {
    errors.value.from = "";
  }

  if (!callLog.value.status) {
    errors.value.status = __("Status is required");
  } else {
    errors.value.status = "";
  }

  if (!callLog.value.duration) {
    errors.value.duration = __("Duration is required");
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

watch(show, (newValue) => {
  if (newValue && props.callLogId) {
    editMode.value = true;
    callLogData.submit({
      name: props.callLogId,
    });
  } else {
    editMode.value = false;
  }
  if (newValue && props.ticketId) {
    callLog.value.ticket = String(props.ticketId);
  }
});
</script>
