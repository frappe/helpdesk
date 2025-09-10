<template>
  <div>
    <div
      v-show="showSmallCallPopup"
      class="ml-2 flex cursor-pointer select-none items-center justify-between gap-1 rounded-full bg-surface-gray-7 px-2 py-1 mt-1 text-base !text-ink-gray-2"
      @click="toggleCallPopup"
    >
      <div
        class="flex justify-center items-center size-5 rounded-full bg-surface-gray-6 shrink-0 mr-1"
      >
        <Avatar
          v-if="contact?.image"
          :image="contact.image"
          :label="contact.full_name"
          class="!size-5"
        />
        <AvatarIcon v-else class="size-3" />
      </div>
      <span>{{
        contact?.full_name ?? (contact?.mobile_no || contact?.phone)
      }}</span>
      <span>·</span>
      <div v-if="callStatus == 'In progress'">
        {{ counterUp?.updatedTime }}
      </div>
      <div
        v-else-if="callStatus == 'Call ended' || callStatus == 'No answer'"
        class="blink"
        :class="{
          'text-red-700':
            callStatus == 'Call ended' || callStatus == 'No answer',
        }"
      >
        <span>{{ callStatus }}</span>
        <span v-if="callStatus == 'Call ended'">
          <span> · </span>
          <span>{{ callDuration }}</span>
        </span>
      </div>
      <div v-else>{{ callStatus }}</div>
    </div>
    <div v-show="showCallPopup" v-bind="$attrs">
      <div
        ref="callPopupHeader"
        class="fixed z-20 flex w-60 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-2 !text-ink-gray-2 shadow-2xl"
        :style="style"
      >
        <div class="flex flex-row-reverse items-center">
          <Button
            @click="closeCallPopup"
            class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6 shrink-0"
            icon="x"
            size="md"
          />
          <Button
            @click="toggleCallPopup"
            variant="ghost"
            class="bg-surface-gray-7 text-ink-white hover:bg-surface-gray-6 shrink-0"
          >
            <MinimizeIcon class="size-4 cursor-pointer" />
          </Button>
        </div>
        <div class="flex flex-col items-center justify-center gap-3">
          <Avatar
            :image="contact.image"
            :label="contact.full_name"
            class="relative flex !h-24 !w-24 items-center justify-center [&>div]:text-[30px]"
            :class="callStatus == 'In progress' ? '' : 'pulse'"
          />
          <div class="flex flex-col items-center justify-center gap-1">
            <div class="text-xl font-medium">
              {{ contact?.full_name ?? "Unknown" }}
            </div>
            <div class="text-sm text-ink-gray-5">
              {{ contact?.mobile_no || contact?.phone }}
            </div>
          </div>
          <CountUpTimer ref="counterUp">
            <div class="my-1 text-base">
              {{ counterUp?.updatedTime }}
            </div>
          </CountUpTimer>
          <div class="my-1 text-base">
            {{ callStatus }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { globalStore } from "@/stores/globalStore";
import { useTelephonyStore } from "@/stores/telephony";
import { useDraggable, useWindowSize } from "@vueuse/core";
import { Avatar, Button, call, toast } from "frappe-ui";
import { inject, onBeforeUnmount, ref, watch } from "vue";
import CountUpTimer from "./CountUpTimer.vue";
import AvatarIcon from "./Icons/AvatarIcon.vue";
import MinimizeIcon from "./Icons/MinimizeIcon.vue";

const telephonyStore = useTelephonyStore();

const onCallStarted = inject<() => void>("onCallStarted");
const onCallEnded = inject<() => void>("onCallEnded");
const onCallFailed = inject<() => void>("onCallFailed");

const callPopupHeader = ref(null);
const showCallPopup = ref(false);
let showSmallCallPopup = ref(false);
const { $socket } = globalStore();
function toggleCallPopup() {
  showCallPopup.value = !showCallPopup.value;
  if (showSmallCallPopup.value == undefined) {
    showSmallCallPopup.value = !showSmallCallPopup.value;
  } else {
    showSmallCallPopup.value = !showSmallCallPopup.value;
  }
}

const { width, height } = useWindowSize();

let { style, x, y } = useDraggable(callPopupHeader, {
  initialValue: { x: width.value - 280, y: height.value - 310 },
  preventDefault: true,
});

watch([width, height], () => {
  x.value = Math.max(0, width.value - 280);
  y.value = Math.max(0, height.value - 310);
});

const callStatus = ref("");
const phoneNumber = ref("");
const callData = ref(null);
const counterUp = ref(null);

const contact = ref({
  full_name: "",
  image: "",
  mobile_no: "",
  phone: "",
});

watch(phoneNumber, (value) => {
  if (!value) return;
  call("telephony.api.get_contact_by_phone_number", {
    phone_number: phoneNumber.value,
  }).then((data) => {
    contact.value = data;
  });
});

function makeOutgoingCall(number) {
  phoneNumber.value = number;

  call("telephony.exotel.handler.make_a_call", {
    to_number: phoneNumber.value,
    link_doctype: telephonyStore.linkDoc.doctype,
    link_docname: telephonyStore.linkDoc.docname,
  })
    .then((callDetails) => {
      callData.value = callDetails;
      callStatus.value = "Calling...";
      showCallPopup.value = true;
      showSmallCallPopup.value = false;
      onCallStarted && onCallStarted();
    })
    .catch((err) => {
      const error = err?.messages?.[0] || "Something went wrong";
      toast.error(error);
      onCallFailed && onCallFailed();
    });
}

function setup(userEmail) {
  $socket.on("exotel_call", (data) => {
    callData.value = data;

    callStatus.value = updateStatus(data);

    if (!showCallPopup.value && !showSmallCallPopup.value) {
      if (data.AgentEmail && data.AgentEmail == userEmail) {
        // Incoming call
        phoneNumber.value = data.CallFrom || data.From;
        showCallPopup.value = true;
      } else {
        // Outgoing call
        phoneNumber.value = data.To;
      }
    }
  });
}

onBeforeUnmount(() => {
  $socket.off("exotel_call");
});

function closeCallPopup() {
  showCallPopup.value = false;
  showSmallCallPopup.value = false;
}

const callDuration = ref("00:00");

function updateStatus(data) {
  // outgoing call
  if (
    data.EventType == "answered" &&
    data.Direction == "outbound-api" &&
    data.Status == "in-progress" &&
    data["Legs[0][Status]"] == "in-progress" &&
    data["Legs[1][Status]"] == ""
  ) {
    return "Ringing...";
  } else if (
    data.EventType == "answered" &&
    data.Direction == "outbound-api" &&
    data.Status == "in-progress" &&
    data["Legs[1][Status]"] == "in-progress"
  ) {
    counterUp.value.start();
    onCallStarted && onCallStarted();
    return "In progress";
  } else if (
    data.EventType == "terminal" &&
    data.Direction == "outbound-api" &&
    (data.Status == "no-answer" || data.Status == "busy") &&
    (data["Legs[1][Status]"] == "no-answer" ||
      data["Legs[0][Status]"] == "no-answer" ||
      data["Legs[1][Status]"] == "busy" ||
      data["Legs[0][Status]"] == "busy")
  ) {
    counterUp.value.stop();
    onCallFailed && onCallFailed();
    return "No answer";
  } else if (
    data.EventType == "terminal" &&
    data.Direction == "outbound-api" &&
    data.Status == "completed"
  ) {
    counterUp.value.stop();
    callDuration.value = counterUp.value.getTime(
      parseInt(data["Legs[0][OnCallDuration]"]) ||
        parseInt(data.DialCallDuration)
    );
    closeCallPopup();
    onCallEnded && onCallEnded();
    return "Call ended";
  }

  // incoming call
  if (
    data.EventType == "Dial" &&
    data.Direction == "incoming" &&
    data.Status == "busy"
  ) {
    phoneNumber.value = data.From || data.CallFrom;
    counterUp.value.start();
    return "Incoming call";
  } else if (
    data.Direction == "incoming" &&
    data.CallType == "incomplete" &&
    data.DialCallStatus == "no-answer"
  ) {
    onCallFailed && onCallFailed();
    counterUp.value.stop();
    return "No answer";
  } else if (
    data.Direction == "incoming" &&
    (data.CallType == "completed" || data.CallType == "client-hangup") &&
    (data.DialCallStatus == "completed" || data.DialCallStatus == "canceled")
  ) {
    onCallEnded && onCallEnded();
    callDuration.value = counterUp.value.getTime(
      parseInt(data["Legs[0][OnCallDuration]"]) ||
        parseInt(data.DialCallDuration)
    );
    closeCallPopup();
    counterUp.value.stop();
    return "Call ended";
  }
}

defineExpose({ makeOutgoingCall, setup });
</script>
<style scoped>
@keyframes blink {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

.blink {
  animation: blink 1s ease-in-out 6;
}

:deep(.ProseMirror) {
  caret-color: var(--ink-white);
}
.pulse::before {
  content: "";
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
}

.pulse::after {
  content: "";
  position: absolute;
  border: 1px solid green;
  width: calc(100% + 20px);
  height: calc(100% + 20px);
  border-radius: 50%;
  animation: pulse 1s linear infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }

  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}
</style>
