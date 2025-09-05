<template>
  <Dialog v-model="show">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __("Call Details") }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager"
              variant="ghost"
              class="w-7"
              @click="openCallLogModal"
              icon="edit"
            />
            <Button
              variant="ghost"
              class="w-7"
              @click="show = false"
              icon="x"
            />
          </div>
        </div>
        <div class="flex flex-col gap-3.5">
          <div
            v-for="field in detailFields"
            :key="field.name"
            class="flex gap-2 text-base text-ink-gray-8"
          >
            <div class="grid size-7 place-content-center">
              <component :is="field.icon" class="size-4 text-ink-gray-8" />
            </div>
            <div class="flex min-h-7 w-full items-center gap-2">
              <div
                v-if="field.name == 'receiver'"
                class="flex items-center gap-1"
              >
                <Avatar
                  :image="field.value.caller.image"
                  :label="field.value.caller.label"
                  size="sm"
                />
                <div class="ml-1 flex flex-col gap-1">
                  {{ field.value.caller.label }}
                </div>
                <FeatherIcon
                  name="arrow-right"
                  class="mx-1 h-4 w-4 text-ink-gray-5"
                />
                <Avatar
                  :image="field.value.receiver.image"
                  :label="field.value.receiver.label"
                  size="sm"
                />
                <div class="ml-1 flex flex-col gap-1">
                  {{ field.value.receiver.label }}
                </div>
              </div>
              <Tooltip v-else-if="field.tooltip" :text="field.tooltip">
                {{ field.value }}
              </Tooltip>
              <div class="w-full" v-else-if="field.name == 'recording_url'">
                <audio
                  class="audio-control w-full"
                  controls
                  :src="field.value"
                ></audio>
              </div>
              <div class="w-full" v-else-if="field.name == 'ticket'">
                <div
                  class="flex items-center gap-1.5 cursor-pointer"
                  @click="() => field.link()"
                >
                  #{{ field.value }}
                  <ArrowUpRightIcon
                    class="h-4 w-4 shrink-0 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
                  />
                </div>
              </div>
              <div v-else :class="field.color ? `text-${field.color}-600` : ''">
                {{ field.value }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import ArrowUpRightIcon from "@/components/icons/ArrowUpRightIcon.vue";
import DurationIcon from "@/components/icons/DurationIcon.vue";
import ContactsIcon from "@/components/icons/ContactsIcon.vue";
import CalendarIcon from "@/components/icons/CalendarIcon.vue";
import CheckCircleIcon from "@/components/icons/CheckCircleIcon.vue";
import TicketIcon from "@/components/icons/TicketIcon.vue";
import { FeatherIcon, Avatar, Tooltip, createResource } from "frappe-ui";
import { computed, h, nextTick, ref, watch } from "vue";
import { formatDate } from "@vueuse/core";
import dayjs from "dayjs";
import { timeAgo } from "@/utils";
import { statusColorMap, statusLabelMap } from "./utils";
import { useAuthStore } from "@/stores/auth";

const show = defineModel();
const callLog = ref(null);
const { isManager } = useAuthStore();

const props = defineProps({
  callLogId: {
    type: String,
    default: "",
  },
  hideTicket: {
    type: Boolean,
    default: false,
  },
});

const callLogData = createResource({
  url: "telephony.api.get_call_log",
  onSuccess(data) {
    callLog.value = data;
  },
  auto: false,
});

const detailFields = computed(() => {
  if (!callLog.value) return [];

  let data = JSON.parse(JSON.stringify(callLog.value));

  for (const key in data) {
    data[key] = getCallLogDetail(key, data);
  }

  let details = [
    {
      icon: h(FeatherIcon, {
        name: data.type.icon,
        class: "h-3.5 w-3.5",
      }),
      name: "type",
      value: data.type.label + " Call",
    },
    {
      icon: ContactsIcon,
      name: "receiver",
      value: {
        receiver: data.receiver,
        caller: data.caller,
      },
    },
    {
      icon: CalendarIcon,
      name: "creation",
      value: data.creation.label,
      tooltip: data.creation.label,
    },
    {
      icon: DurationIcon,
      name: "duration",
      value: data.duration.label,
    },
    {
      icon: CheckCircleIcon,
      name: "status",
      value: data.status.label,
      color: data.status.color,
    },
    {
      icon: h(FeatherIcon, {
        name: "play-circle",
        class: "h-4 w-4 mt-2",
      }),
      name: "recording_url",
      value: data.recording_url,
    },
  ];

  const ticketLink = data.links?.find(
    (link) => link.link_doctype == "HD Ticket"
  );

  if (ticketLink && !props.hideTicket) {
    details.push({
      icon: TicketIcon,
      name: "ticket",
      value: ticketLink.link_name,
      link: () => {
        window.open(`/helpdesk/tickets/${ticketLink.link_name}`);
      },
    });
  }

  return details.filter((detail) => detail.value);
});

const showCallLogModal = defineModel("callLogModal");

function openCallLogModal() {
  showCallLogModal.value = true;
  nextTick(() => {
    show.value = false;
  });
}

function getCallLogDetail(row, log, columns = []) {
  let incoming = log.type === "Incoming";

  if (row === "duration") {
    return {
      label: log._duration,
      icon: "clock",
    };
  } else if (row === "caller") {
    return {
      label: log._caller?.label,
      image: log._caller?.image,
    };
  } else if (row === "receiver") {
    return {
      label: log._receiver?.label,
      image: log._receiver?.image,
    };
  } else if (row === "type") {
    return {
      label: log.type,
      icon: incoming ? "phone-incoming" : "phone-outgoing",
    };
  } else if (row === "status") {
    return {
      label: statusLabelMap[log.status],
      color: statusColorMap[log.status],
    };
  } else if (["modified", "creation"].includes(row)) {
    return {
      label: dayjs(log[row]).format("ddd, MMM D, YYYY h:mm a"),
      timeAgo: timeAgo(log[row]),
    };
  }

  let fieldType = columns?.find((col) => (col.key || col.value) == row)?.type;

  if (fieldType && ["Date", "Datetime"].includes(fieldType)) {
    return formatDate(log[row], "");
  }

  return log[row];
}

watch(show, (newValue) => {
  if (newValue && props.callLogId) {
    callLogData.submit({
      name: props.callLogId,
    });
  }
});
</script>

<style scoped>
.audio-control {
  height: 36px;
  outline: none;
  border-radius: 10px;
  cursor: pointer;
  background-color: rgb(237, 237, 237);
}

audio::-webkit-media-controls-panel {
  background-color: rgb(237, 237, 237) !important;
}

.audio-control::-webkit-media-controls-panel {
  background-color: white;
}
</style>
