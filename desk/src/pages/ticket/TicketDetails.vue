<template>
  <div class="flex flex-col">
    <div class="border-l">
      <span>
        <TicketSidebarHeader title="Details" />
        <div class="mx-5 my-6 flex flex-col justify-between gap-3.5 text-base">
          <div class="space-y-1.5">
            <span class="block text-sm text-gray-700">ID</span>
            <span class="block break-words font-medium text-gray-900">
              {{ data.name }}
            </span>
          </div>
          <div v-if="data.customer" class="space-y-1.5">
            <span class="block text-sm text-gray-700">Customer</span>
            <span class="block break-words font-medium text-gray-900">
              {{ data.customer }}
            </span>
          </div>
          <div
            v-if="data.first_responded_on || data.response_by"
            class="space-y-1.5"
          >
            <div class="text-sm text-gray-700">First response</div>
            <div class="mr-2 inline-block font-medium text-gray-900">
              {{ dayjs(data.first_responded_on || data.response_by).short() }}
            </div>
            <span v-if="data.response_by">
              <Badge
                v-if="!data.first_responded_on"
                label="Due"
                theme="orange"
                variant="outline"
              />
              <Badge
                v-else-if="
                  dayjs(data.first_responded_on).isBefore(
                    dayjs(data.response_by)
                  )
                "
                label="Fulfilled"
                theme="green"
                variant="outline"
              />
              <Badge v-else label="Failed" theme="red" variant="outline" />
            </span>
          </div>
          <div
            v-if="data.resolution_date || data.resolution_by"
            class="space-y-1.5"
          >
            <span class="block text-sm text-gray-700">Resolution</span>
            <span class="mr-2 font-medium text-gray-900">
              {{ dayjs(data.resolution_date || data.resolution_by).short() }}
            </span>
            <Badge
              v-if="
                dayjs(data.resolution_date || undefined).isAfter(
                  data.resolution_by
                )
              "
              label="Failed"
              theme="red"
              variant="outline"
            />
            <Badge
              v-else-if="!data.resolution_date"
              label="Due"
              theme="orange"
              variant="outline"
            />
            <Badge
              v-else-if="
                dayjs(data.resolution_date).isBefore(data.resolution_by)
              "
              label="Fulfilled"
              theme="green"
              variant="outline"
            />
          </div>
          <div class="space-y-1.5">
            <span class="block text-sm text-gray-700">Modified</span>
            <Tooltip :text="dayjs(ticket.data.modified).long()">
              <span class="block break-words font-medium text-gray-900">
                {{ dayjs(ticket.data.modified).fromNow() }}
              </span>
            </Tooltip>
          </div>
          <div class="space-y-1.5">
            <span class="block text-sm text-gray-700">Source</span>
            <span class="block break-words font-medium text-gray-900">
              {{ ticket.data.via_customer_portal ? "Portal" : "Mail" }}
            </span>
          </div>
          <div v-if="data.feedback_rating" class="space-y-1.5">
            <span class="block text-sm text-gray-700">Feedback</span>
            <StarRating :rating="data.feedback_rating" />
            <span class="block font-medium text-gray-900">
              {{ data.feedback_text }}
            </span>
            <span class="block text-gray-900">
              {{ data.feedback_extra }}
            </span>
          </div>
        </div>
      </span>
    </div>
    <div v-if="data.status !== 'Closed' && data.status !== 'Resolved' && enableTimeTracking" class="divider"></div>
    <div class="border-l">
      <span>
        <div
          v-if="data.status !== 'Closed' && data.status !== 'Resolved' && enableTimeTracking"
          class="mx-5 my-6 flex flex-col justify-between text-base"
        >
          <div class="space-y-1.5">
            <span class="mr-2 font-medium text-gray-900">
              Time Tracking
            </span>
            <Badge
              v-if="timerState === 'running'"
              label="Running"
              theme="red"
              variant="outline"
            />
            <Badge
              v-else-if="timerState === 'paused'"
              label="Paused"
              theme="red"
              variant="outline"
            />
            <Badge v-else label="Idle" theme="green" variant="outline" />
          </div>
          <div class="space-y-1.5">
            <TabGroup horizontal>
              <TabList>
                <tab v-for="item in timeritems" :key="item.name">
                  <Tooltip
                    v-if="timerState === item.state"
                    :text="item.name"
                    placement="left"
                  >
                    <div
                      class="justify-left flex h-7 w-7 items-center rounded-full text-gray-900 transition-all"
                      :class="{
                        shadow: isExpanded && selected,
                        'bg-gray-50': isExpanded && selected,
                      }"
                      @click="item.click"
                    >
                      <component :is="item.icon" class="h-4 w-4" />
                    </div>
                  </Tooltip>
                </tab>
              </TabList>
            </TabGroup>
          </div>
          <div
            v-if="timerState === 'running' || timerState === 'paused'"
            class="space-y-1.5"
          >
            <span class="block text-sm text-gray-700">Live Duration</span>
            <span class="block font-medium text-gray-900">{{
              formattedElapsedTime
            }}</span>
          </div>
        </div>
      </span>
    </div>
    <div class="divider"></div>
    <div
      class="flex grow flex-col gap-3 truncate border-l p-5"
      :style="{
        'overflow-y': 'scroll',
      }"
    >
      <div v-for="o in options" :key="o.field" class="space-y-1.5">
        <span class="block text-sm text-gray-700">
          {{ o.label }}
        </span>
        <Autocomplete
          :options="o.store.dropdown"
          :placeholder="`Select a ${o.label}`"
          :value="data[o.field]"
          @change="update(o.field, $event.value)"
        />
      </div>
      <UniInput
        v-for="field in data.template.fields"
        :key="field.fieldname"
        :field="field"
        :value="data[field.fieldname]"
        @change="update(field.fieldname, $event.value)"
      />
    </div>
  </div>
  <TimeEntryDialog :elapsed-time-initial="elapsed.value" ref="timeEntryDialog" @submit="handleDialogClose" />
</template>

<script setup lang="ts">
import { ref, computed, inject, onMounted, onUnmounted, watch } from "vue";
import { createResource, Autocomplete, Tooltip, debounce } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { emitter } from "@/emitter";
import { createToast } from "@/utils";
import { useTeamStore } from "@/stores/team";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketTypeStore } from "@/stores/ticketType";
import { useError } from "@/composables/error";
import { StarRating, UniInput } from "@/components";
import TicketSidebarHeader from "./TicketSidebarHeader.vue";
import { ITicket } from "./symbols";
import LucidePlay from "~icons/lucide/play";
import LucidePause from "~icons/lucide/pause";
import LucideComplete from "~icons/lucide/check";
import { TabGroup, TabList, Tab } from "@headlessui/vue";
import TimeEntryDialog from "@/components/desk/global/AddTicketTimeEntryDialog.vue";

const ticket = inject(ITicket);
const data = computed(() => ticket.data);
const timerState = ref("idle");
const startTime = ref(null);
const elapsed = ref(0);
const maxDuration = ref(0);
const currentEntryId = ref(null);
const timerInterval = ref(null);
const userId = getUserIdFromCookies();
const timeEntryDialog = ref(null);
const maxDurationNotified = ref(false);
const activeTimerStartTime = ref<number | null>(null);
const finalElapsedBeforeDialog = ref(0);
const maxDurationReached = ref(false); 

const options = computed(() => [
  {
    field: "ticket_type",
    label: "Ticket type",
    store: useTicketTypeStore(),
  },
  {
    field: "priority",
    label: "Priority",
    store: useTicketPriorityStore(),
  },
  {
    field: "agent_group",
    label: "Team",
    store: useTeamStore(),
  },
]);

const timeritems = [
  {
    name: "Start",
    click: startTimer,
    state: "idle",
    icon: LucidePlay,
  },
  {
    name: "Pause",
    click: pauseTimer,
    state: "running",
    icon: LucidePause,
  },
  {
    name: "Resume",
    click: resumeTimer,
    state: "paused",
    icon: LucidePlay,
  },
  {
    name: "Complete",
    click: recordtimeentry,
    state: "running",
    icon: LucideComplete,
  },
];

const formattedElapsedTime = computed(() => {
  let elapsedTimeCalculation = elapsed.value;

  if (timerState.value === "running") {
    const now = Date.now();
    elapsedTimeCalculation += now - startTime.value;
  }
  const seconds = Math.floor((elapsedTimeCalculation / 1000) % 60);
  const minutes = Math.floor((elapsedTimeCalculation / (1000 * 60)) % 60);
  const hours = Math.floor((elapsedTimeCalculation / (1000 * 60 * 60)) % 24);

  return `${hours.toString().padStart(2, "0")}:${minutes
    .toString()
    .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
});

const unwatch = watch(data, () => {
  if (timerState.value === "running" || timerState.value === "paused") {
    storeTimerState(
      data.value.name,
      currentEntryId.value,
      timerState.value,
      elapsed.value
    );
  }
});

let beforeUnloadHandlerAdded = false;
let enableTimeTracking = ref(false);

onMounted(() => {
  fetchTimeSettings().then(() => {
    if (enableTimeTracking.value) {
      initializeTimer();
      setupBeforeUnloadHandler();
    }
  });
});

onUnmounted(() => {
  clearInterval(timerInterval.value);
  unwatch();
});

watch(timerState, (newValue) => {
  if (newValue === "running") {
    activeTimerStartTime.value = Date.now();
  } else if (newValue === "paused") {
    activeTimerStartTime.value = null;
  }
});

async function fetchTimeSettings() {
  try {
      const customer = ticket.data.customer;
      const url = new URL("/api/method/helpdesk.helpdesk.doctype.hd_settings.hd_settings.get_timetracking_settings", window.location.origin);
      if (customer) {
          url.searchParams.append('customer', customer);
      }
      const response = await fetch(url, {
          method: "GET",
          headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
              "X-Frappe-CSRF-Token": window.csrf_token,
          },
      });
      if (response.ok) {
          const data = await response.json();
          if(data.message) {
            enableTimeTracking.value = data.message.enableTimeTracking;
            maxDuration.value = data.message.maxDuration;
          }
      }
  } catch (error) {
      console.error('Error fetching time settings:', error);
  }
}

function update(fieldname, value) {
  createResource({
    url: "frappe.client.set_value",
    debounce: 300,
    params: {
      doctype: "HD Ticket",
      name: data.value.name,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      emitter.emit("update:ticket");
      createToast({
        title: "Ticket updated",
        icon: "check",
        iconClasses: "text-green-600",
      });
    },
    onError: useError(),
  });
}

function setupBeforeUnloadHandler() {
  const handleBeforeUnload = (_event) => {
    if (timerState.value !== "idle") {
      storeTimerState(
        data.value.name,
        currentEntryId.value,
        timerState.value,
        elapsed.value
      );
    }
  };

  if (!beforeUnloadHandlerAdded) {
    window.addEventListener("beforeunload", handleBeforeUnload);
    beforeUnloadHandlerAdded = true;

    onUnmounted(() => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      beforeUnloadHandlerAdded = false;
    });
  }
}

function startTimer() {
  manageTimer("start").catch(console.error);
}

function pauseTimer() {
  manageTimer("pause").catch(console.error);
}

async function resumeTimer() {
  manageTimer("resume").catch(console.error);
}

async function completeTimer(payload) {
  const { description, elapsedtime, override_duration } = payload;
  await manageTimer("complete", { description, elapsedtime, override_duration });
}

async function manageTimer(action, { description = "", elapsedtime = null, override_duration = null } = {}) {
  try {
    switch (action) {
      case "start":
        if (timerState.value === "idle") {
          currentEntryId.value = null;
          startTime.value = Date.now();
          elapsed.value = 0;
          timerState.value = "running";
          setupInterval();
          storeTimerState();
        }
        break;
      case "resume":
        if (timerState.value === "paused") {
          startTime.value = Date.now(); // Adjust if resuming should not reset startTime
          timerState.value = "running";
          setupInterval();
          storeTimerState();
        }
        break;
      case "pause":
        if (timerState.value === "running") {
          clearInterval(timerInterval.value);
          const now = Date.now();
          elapsed.value += now - startTime.value;
          timerState.value = "paused";
          storeTimerState();
        }
        break;
      case "complete":
        if (timerState.value !== "idle") {
          clearInterval(timerInterval.value);
          timerState.value = "idle";
          let payloadData = {
            ticketId: data.value.name,
            agent: userId,
            name: currentEntryId.value,
            duration: elapsedtime,
            description: description,
            maximum_duration_reached: maxDurationReached.value,
          };
          
          if (override_duration !== null) {
            payloadData.override_duration = override_duration;
          }
          await debouncedCreateOrUpdateTimeEntry(action, payloadData);
          resetTimerState();
          emitter.emit("update:ticket");
        }
        return; // Early return to prevent duplicate backend call for 'complete'
    }

    if (action !== "complete") {
      let payloadData = {
        ticketId: data.value.name,
        agent: userId,
        name: currentEntryId.value,
        duration: elapsed.value,
        maximum_duration_reached: maxDurationReached.value,
      };

      await debouncedCreateOrUpdateTimeEntry(action, payloadData);
    }

    // Additional logic for max duration check, etc., remains here
  } catch (error) {
    console.error(`Error managing timer: ${error}`);
    createToast({
      title: "Error",
      description: `Failed to ${action} timer due to an error.`,
      type: "error",
    });
  }
}

async function recordtimeentry(maxDurationReached) {
  pauseTimer();
  if (maxDurationReached.value) {
    createToast({
      title: "Max Duration Reached",
      description: "Please complete the time entry.",
      type: "warning",
    });
  }
  // For manual completion, show the dialog without max duration reached warning
  timeEntryDialog.value.showDialog(elapsed.value);
}

async function handleDialogClose(payload) {
  await completeTimer(payload);
  maxDurationNotified.value = false;
  finalElapsedBeforeDialog.value = 0;
}

async function createOrUpdateTimeEntry(action, data) {
  const apiEndpoint = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.create_or_update_time_entry";
  const payload = {
    ticket_id: data.ticketId,
    agent: userId,
    action: action,
    duration: data.duration || null,
    name: currentEntryId.value || null,
    maximum_duration_reached: maxDurationReached.value,
    description: data.description || "",
    override_duration: data.override_duration || null
  };
  
  try {
      const response = await fetch(apiEndpoint, {
          method: "POST",
          headers: {
              "Content-Type": "application/json",
              "X-Frappe-CSRF-Token": window.csrf_token,
          },
          body: JSON.stringify(payload),
      });
      if (!response.ok) {
            throw new Error(`Failed to update time entry on the backend. Status: ${response.status}`);
      }

      const responseData = await response.json();
      if (responseData.message && responseData.message.name) {
          currentEntryId.value = responseData.message.name;
      }
      return responseData;
  } catch (error) {
        console.error("Error creating or updating time entry:", error);
        // Handle error appropriately (e.g., user notification, state rollback)
        throw error; // Re-throw to allow caller to handle
  }
}

function resetTimerState() {
  timerState.value = "idle";
  elapsed.value = 0;
  startTime.value = null;
  clearInterval(timerInterval.value);
  clearTimerState();
  maxDurationNotified.value = false;
}

function setupInterval() {
  clearInterval(timerInterval.value);
  timerInterval.value = setInterval(() => {
    if (timerState.value === 'running') {
        updateElapsedTime();
        checkAndHandleMaxDuration();
    }
  }, 1000);
}

// This example assumes maxDurationReached is a ref and maxDurationNotified prevents repetitive notifications
function checkAndHandleMaxDuration() {
  if (maxDuration.value === null) {
    return;
  }
  const now = Date.now();
  const newElapsed = elapsed.value + (now - (startTime.value || now)); // Safeguard against null startTime
  
  if (newElapsed >= maxDuration.value && !maxDurationReached.value) {
    maxDurationReached.value = true;
    maxDurationNotified.value = true;
    // Open dialog if max duration reached
    recordtimeentry(true);
  }
}

function getUserIdFromCookies() {
  const cookies = document.cookie.split(";");
  let userId = "";

  cookies.forEach((cookie) => {
    const [key, value] = cookie.split("=").map((part) => part.trim());
    if (key === "user_id") {
      userId = decodeURIComponent(value);
    }
  });
  return userId;
}

function storeTimerState() {
  const timerInfo = {
    ticketId: data.value.name,
    timeEntryId: currentEntryId.value,
    timerState: timerState.value,
    elapsed: elapsed.value,
    startTime: startTime.value,
  };
  localStorage.setItem("runningTimer", JSON.stringify(timerInfo));
}

function updateElapsedTime() {
  const now = Date.now();
  elapsed.value += now - (startTime.value || now); // This ensures `elapsed` changes, triggering reactivity.
  startTime.value = now; // Update startTime to now after each tick to ensure continuous calculation.
}

function getStoredTimerState() {
  const runningTimer = localStorage.getItem("runningTimer");
  if (!runningTimer) return null;
  return JSON.parse(runningTimer);
}

async function initializeTimer() {
  const storedTimer = getStoredTimerState();
  if (storedTimer && storedTimer.ticketId === data.value.name) {
    const isActive = await isTimeEntryActive(storedTimer.timeEntryId);
    if (isActive.is_active || storedTimer.timerState === "running" || storedTimer.timerState === "paused") {
      timerState.value = storedTimer.timerState.toLowerCase();
      currentEntryId.value = storedTimer.timeEntryId;
      startTime.value = storedTimer.startTime
        ? new Date(storedTimer.startTime).getTime()
        : null;
      elapsed.value = storedTimer.elapsed;

      if (timerState.value === "paused") {
      } else if (timerState.value === "running") {
        const now = Date.now();
        if (startTime.value) {
          const additionalElapsed = now - startTime.value;
          elapsed.value += additionalElapsed;
          startTime.value = now;
        }
        setupInterval();
      }
    } else {
      resetTimer();
    }
  } else {
    resetTimer();
  }
}

async function isTimeEntryActive(timeEntryId) {
  try {
    const response = await fetch(
      `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.is_time_entry_running`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Frappe-CSRF-Token": window.csrf_token,
        },
        body: JSON.stringify({ time_entry_id: timeEntryId }),
      }
    );
    if (!response.ok) {
      throw new Error("Network response was not ok.");
    }
    const data = await response.json();
    return data.message === true;
  } catch (error) {
    console.error("Error checking time entry status:", error);
    return false;
  }
}

function resetTimer() {
  timerState.value = "idle";
  currentEntryId.value = null;
  elapsed.value = 0;
  startTime.value = null;
  clearInterval(timerInterval.value);
  timerInterval.value = null;
}

function clearTimerState() {
  localStorage.removeItem("runningTimer");
}

// Debounced wrapper function
const debouncedCreateOrUpdateTimeEntry = debounce(async (action, data) => {
  try {
    await createOrUpdateTimeEntry(action, data);
  } catch (error) {
    console.error("Debounced function error:", error);
  }
}, 300);
</script>

<style scoped>
.divider {
  border-bottom: 1px solid #e2e2e2;
  border-style: dashed;
  position: relative;
}

.divider:before {
  position: absolute;
  bottom: -14px;
  left: 0;
  height: 28px;
  width: 14px;
  background: white;
  content: "";
  border-top-right-radius: 9999px;
  border-bottom-right-radius: 9999px;
  border-right-width: 1px;
  border-top-width: 1px;
  border-bottom-width: 1px;
}

.divider:after {
  position: absolute;
  bottom: -14px;
  left: 0;
  height: 28px;
  width: 14px;
  background: white;
  content: "";
  border-top-left-radius: 9999px;
  border-bottom-left-radius: 9999px;
  border-left-width: 1px;
  border-top-width: 1px;
  border-bottom-width: 1px;
}

.divider:after {
  right: 0;
  left: auto;
}
</style>
