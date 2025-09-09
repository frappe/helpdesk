<template>
  <div v-show="showCallPopup" v-bind="$attrs">
    <div
      ref="callPopup"
      class="fixed z-20 flex w-60 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-4 !text-ink-gray-2 shadow-2xl"
      :style="style"
    >
      <div class="flex flex-row-reverse items-center gap-1">
        <MinimizeIcon
          class="h-4 w-4 cursor-pointer"
          @click="toggleCallWindow"
        />
      </div>
      <div class="flex flex-col items-center justify-center gap-3">
        <Avatar
          :image="contact?.image"
          :label="contact?.full_name"
          class="relative flex !h-24 !w-24 items-center justify-center [&>div]:text-[30px]"
          :class="onCall || calling ? '' : 'pulse'"
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
          <div v-if="onCall" class="my-1 text-base">
            {{ counterUp?.updatedTime }}
          </div>
        </CountUpTimer>
        <div v-if="!onCall" class="my-1 text-base">
          {{
            callStatus == "initiating"
              ? "Initiating call..."
              : callStatus == "ringing"
              ? "Ringing..."
              : calling
              ? "Calling..."
              : "Incoming call..."
          }}
        </div>
        <div v-if="onCall" class="flex gap-2">
          <Button
            :icon="muted ? 'mic-off' : 'mic'"
            class="rounded-full"
            @click="toggleMute"
          />
          <Button
            class="rounded-full bg-surface-red-5 hover:bg-surface-red-6"
            @click="hangUpCall"
          >
            <template #icon>
              <LucidePhone class="h-4 w-4 rotate-[135deg] text-ink-white" />
            </template>
          </Button>
        </div>
        <div v-else-if="calling || callStatus == 'initiating'">
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="'Cancel'"
            @click="cancelCall"
            class="rounded-lg"
          >
            <template #prefix>
              <LucidePhone class="h-4 w-4 rotate-[135deg]" />
            </template>
          </Button>
        </div>
        <div v-else class="flex gap-2">
          <Button
            size="md"
            variant="solid"
            theme="green"
            :label="'Accept'"
            class="rounded-lg"
            @click="acceptIncomingCall"
          >
            <template #prefix>
              <LucidePhone class="h-4 w-4" />
            </template>
          </Button>
          <Button
            size="md"
            variant="solid"
            theme="red"
            :label="'Reject'"
            class="rounded-lg"
            @click="rejectIncomingCall"
          >
            <template #prefix>
              <LucidePhone class="h-4 w-4 rotate-[135deg]" />
            </template>
          </Button>
        </div>
      </div>
    </div>
  </div>
  <div
    v-show="showSmallCallWindow"
    class="ml-2 mt-1 flex cursor-pointer select-none items-center justify-between gap-3 rounded-lg bg-surface-gray-7 px-2 py-1 text-base !text-ink-gray-2"
    @click="toggleCallWindow"
    v-bind="$attrs"
  >
    <div class="flex items-center gap-2">
      <Avatar
        :image="contact?.image"
        :label="contact?.full_name"
        class="relative flex !h-5 !w-5 items-center justify-center"
      />
      <div class="max-w-[120px] truncate">
        {{ contact?.full_name ?? "Unknown" }}
      </div>
    </div>
    <div v-if="onCall" class="flex items-center gap-2">
      <div class="my-1 min-w-[40px] text-center">
        {{ counterUp?.updatedTime }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full"
        @click.stop="hangUpCall"
      >
        <template #icon>
          <LucidePhone class="h-4 w-4 rotate-[135deg]" />
        </template>
      </Button>
    </div>
    <div v-else-if="calling" class="flex items-center gap-3">
      <div class="my-1">
        {{ callStatus == "ringing" ? "Ringing..." : "Calling..." }}
      </div>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full"
        @click.stop="cancelCall"
      >
        <template #icon>
          <LucidePhone class="h-4 w-4 rotate-[135deg]" />
        </template>
      </Button>
    </div>
    <div v-else class="flex items-center gap-2">
      <Button
        variant="solid"
        theme="green"
        class="pulse relative !h-6 !w-6 rounded-full"
        @click.stop="acceptIncomingCall"
      >
        <template #icon>
          <LucidePhone class="h-4 w-4 animate-pulse" />
        </template>
      </Button>
      <Button
        variant="solid"
        theme="red"
        class="!h-6 !w-6 rounded-full"
        @click.stop="rejectIncomingCall"
      >
        <template #icon>
          <LucidePhone class="h-4 w-4 rotate-[135deg]" />
        </template>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTelephonyStore } from "@/stores/telephony";
import { Call, Device } from "@twilio/voice-sdk";
import { useDraggable, useWindowSize } from "@vueuse/core";
import { Avatar, call, toast } from "frappe-ui";
import { inject, ref, watch } from "vue";
import LucidePhone from "~icons/lucide/phone";
import CountUpTimer from "./CountUpTimer.vue";
import MinimizeIcon from "./Icons/MinimizeIcon.vue";

const telephonyStore = useTelephonyStore();

const onCallStarted = inject<() => void>("onCallStarted");
const onCallEnded = inject<() => void>("onCallEnded");
const onCallFailed = inject<() => void>("onCallFailed");

let device: Device | null = null;
let log = ref("");
let _call = null;

let showCallPopup = ref(false);
let showSmallCallWindow = ref(false);
let onCall = ref(false);
let calling = ref(false);
let muted = ref(false);
let callPopup = ref(null);
let counterUp = ref(null);
let callStatus = ref("");

const phoneNumber = ref("");

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

const { width, height } = useWindowSize();

let { x, y, style } = useDraggable(callPopup, {
  initialValue: { x: width.value - 280, y: height.value - 310 },
  preventDefault: true,
});

watch([width, height], () => {
  x.value = Math.max(0, width.value - 280);
  y.value = Math.max(0, height.value - 310);
});

async function startupClient() {
  log.value = "Requesting Access Token...";

  try {
    const data = await call("telephony.twilio.api.generate_access_token");
    log.value = "Got a token.";
    intitializeDevice(data.token);
  } catch (err) {
    log.value = "An error occurred. " + err.message;
  }
}

function intitializeDevice(token) {
  device = new Device(token, {
    codecPreferences: [Call.Codec.Opus, Call.Codec.PCMU],
  });

  addDeviceListeners();

  device.register();
}

function addDeviceListeners() {
  device.on("registered", () => {
    log.value = "Ready to make and receive calls!";
  });

  device.on("unregistered", (device) => {
    log.value = "Logged out";
  });

  device.on("error", (error) => {
    log.value = "Twilio.Device Error: " + error.message;
  });

  device.on("incoming", handleIncomingCall);

  device.on("tokenWillExpire", async () => {
    const data = await call("telephony.twilio.api.generate_access_token");
    device.updateToken(data.token);
  });
}

function toggleMute() {
  if (_call.isMuted()) {
    _call.mute(false);
    muted.value = false;
  } else {
    _call.mute();
    muted.value = true;
  }
}

function handleIncomingCall(call) {
  log.value = `Incoming call from ${call.parameters.From}`;
  phoneNumber.value = call.parameters.From;

  showCallPopup.value = true;
  _call = call;

  // add event listener to call object
  call.on("cancel", handleDisconnectedIncomingCall);
  call.on("disconnect", handleDisconnectedIncomingCall);
  call.on("reject", handleDisconnectedIncomingCall);
}

async function acceptIncomingCall() {
  log.value = "Accepted incoming call.";
  onCall.value = true;
  await _call.accept();
  onCallStarted && onCallStarted();
  counterUp.value.start();
}

function rejectIncomingCall() {
  _call.reject();
  log.value = "Rejected incoming call";
  showCallPopup.value = false;
  if (showSmallCallWindow.value == undefined) {
    showSmallCallWindow.value = false;
  } else {
    showSmallCallWindow.value = false;
  }
  callStatus.value = "";
  muted.value = false;
  onCallFailed && onCallFailed();
}

function hangUpCall() {
  _call.disconnect();
  log.value = "Hanging up incoming call";
  onCall.value = false;
  callStatus.value = "";
  muted.value = false;
  counterUp.value.stop();
  onCallEnded && onCallEnded();
}

function handleDisconnectedIncomingCall() {
  log.value = `Call ended from handle disconnected Incoming call.`;
  showCallPopup.value = false;
  if (showSmallCallWindow.value == undefined) {
    showSmallCallWindow.value = false;
  } else {
    showSmallCallWindow.value = false;
  }
  _call = null;
  muted.value = false;
  onCall.value = false;
  counterUp.value.stop();
  onCallEnded && onCallEnded();
}

async function makeOutgoingCall(number) {
  phoneNumber.value = number;

  if (device) {
    log.value = `Attempting to call ${number} ...`;
    onCallStarted && onCallStarted();

    try {
      _call = await device.connect({
        params: {
          To: number,
          link_doctype: telephonyStore.linkDoc.doctype,
          link_docname: telephonyStore.linkDoc.docname,
        },
      });

      showCallPopup.value = true;
      callStatus.value = "initiating";

      _call.on("messageReceived", (message) => {
        let info = message.content;
        callStatus.value = info.CallStatus;

        log.value = `Call status: ${info.CallStatus}`;

        if (info.CallStatus == "in-progress") {
          log.value = `Call in progress.`;
          calling.value = false;
          onCall.value = true;
          counterUp.value.start();
        }
      });

      _call.on("accept", () => {
        log.value = `Initiated call!`;
        showCallPopup.value = true;
        calling.value = true;
        onCall.value = false;
      });
      _call.on("disconnect", (conn) => {
        log.value = `Call ended from makeOutgoing call disconnect.`;
        calling.value = false;
        onCall.value = false;
        showCallPopup.value = false;
        showSmallCallWindow.value = false;
        _call = null;
        callStatus.value = "";
        muted.value = false;
        counterUp.value.stop();
        onCallEnded && onCallEnded();
      });
      _call.on("cancel", () => {
        log.value = `Call ended from makeOutgoing call cancel.`;
        calling.value = false;
        onCall.value = false;
        showCallPopup.value = false;
        showSmallCallWindow.value = false;
        _call = null;
        callStatus.value = "";
        muted.value = false;
        counterUp.value.stop();
        onCallEnded && onCallEnded();
      });
    } catch (error) {
      onCallFailed && onCallFailed();
      log.value = `Could not connect call: ${error.message}`;
      toast.error(error.message);
    }
  } else {
    onCallFailed && onCallFailed();
    log.value = "Unable to make call.";
    toast.error("Unable to make call.");
  }
}

function cancelCall() {
  _call.disconnect();
  showCallPopup.value = false;
  if (showSmallCallWindow.value == undefined) {
    showSmallCallWindow.value = false;
  } else {
    showSmallCallWindow.value = false;
  }
  calling.value = false;
  onCall.value = false;
  callStatus.value = "";
  muted.value = false;
}

function toggleCallWindow() {
  showCallPopup.value = !showCallPopup.value;
  if (showSmallCallWindow.value == undefined) {
    showSmallCallWindow.value = !showSmallCallWindow;
  } else {
    showSmallCallWindow.value = !showSmallCallWindow.value;
  }
}

watch(
  () => log.value,
  (value) => {
    console.log(value);
  },
  { immediate: true }
);

defineExpose({ makeOutgoingCall, setup: startupClient });
</script>

<style scoped>
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
