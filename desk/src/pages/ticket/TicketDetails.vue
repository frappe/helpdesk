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
          <div
            v-if="data.status !== 'Closed' && data.status !== 'Resolved'"
            class="space-y-1.5"
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
</template>

<script setup lang="ts">
import { ref, computed, inject, onMounted, onUnmounted, watch } from "vue";
import { createResource, Autocomplete, Tooltip } from "frappe-ui";
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

const ticket = inject(ITicket);
const data = computed(() => ticket.data);

// Time tracking state
const timerState = ref("idle");
const startTime = ref(null);
const elapsed = ref(0);
const maxDuration = 28800000; // 8 hours in milliseconds
const currentEntryId = ref(null); // Assuming you have a mechanism to track this ID
const timerInterval = ref(null);
const userId = getUserIdFromCookies();

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
    click: completeTimer,
    state: "running",
    icon: LucideComplete,
  },
];

// Define a reactive variable to store the start time of the active timer
const activeTimerStartTime = ref<number | null>(null);

// Define a computed property to calculate the elapsed time in seconds
const elapsedTimeInSeconds = computed(() => {
  if (activeTimerStartTime.value === null) {
    return 0;
  } else {
    const currentTime = Date.now();
    return Math.floor((currentTime - activeTimerStartTime.value) / 1000);
  }
});

// Define a computed property to format the elapsed time in HH:MM:SS format
const formattedElapsedTime = computed(() => {
  if (timerState.value === "running" || timerState.value === "paused") {
    const now = Date.now();
    const elapsedMs = now - startTime.value + elapsed.value;
    const seconds = Math.floor((elapsedMs / 1000) % 60);
    const minutes = Math.floor((elapsedMs / (1000 * 60)) % 60);
    const hours = Math.floor((elapsedMs / (1000 * 60 * 60)) % 24);

    return `${hours.toString().padStart(2, "0")}:${minutes
      .toString()
      .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  }
  return "00:00:00";
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

let wasTimerRunningOnLoad = false;

onMounted(() => {
  console.log("Component mounted, initializing timer...");
  initializeTimer();
});

onUnmounted(() => {
  console.log("Component unmounted, unwatch...");
  console.log("Timer State: " + timerState.value);
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

function update(fieldname: string, value: string) {
  createResource({
    url: "frappe.client.set_value",
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

async function startTimer(isRestoration = false) {
  currentEntryId.value = null;
  timerState.value = "running";
  startTime.value = Date.now();
  elapsed.value = 0;
  clearInterval(timerInterval.value);

  try {
    const response = await createOrUpdateTimeEntry({
      ticket_id: data.value.name,
      agent: userId,
      action: "start",
      duration: null,
      max_duration_reached: false,
    });
    currentEntryId.value = response.name;
    console.log("Timer State: " + timerState.value);
    storeTimerState(data.value.name, response.name, "running", 0);
    setupInterval();
    timerInterval.value = setInterval(() => {
      const currentElapsed = Date.now() - startTime.value;
      let elapsedSinceStart =
        Date.now() - startTime.value + (elapsed.value || 0);
      if (elapsedSinceStart >= maxDuration) {
        console.log(
          "startTimer MaxDuration has been hit: " + elapsedSinceStart
        );
        elapsedSinceStart = maxDuration;
        completeTimer(true);
      }
    }, 1000);
  } catch (error) {
    console.error("Error starting time entry:", error);
  }
}

async function pauseTimer() {
  if (timerState.value === "running") {
    timerState.value = "paused";
    clearInterval(timerInterval.value);
    updateElapsed(true);

    try {
      const response = await createOrUpdateTimeEntry({
        ticket_id: data.value.name,
        agent: userId,
        name: currentEntryId.value,
        duration: elapsed.value,
        action: "pause",
        max_duration_reached: elapsed.value >= maxDuration,
      });
      console.log("Pause response:", response);
      storeTimerState(); // Make sure this reflects the paused state accurately
    } catch (error) {
      console.error("Error pausing time entry:", error);
    }
  }
}

async function resumeTimer() {
  if (timerState.value === "paused") {
    const now = Date.now();
    startTime.value = now;
    timerState.value = "running";
    setupInterval();

    try {
      const response = await createOrUpdateTimeEntry({
        ticket_id: data.value.name,
        agent: userId,
        name: currentEntryId.value,
        duration: elapsed.value,
        action: "resume",
        max_duration_reached: false,
      });
      console.log("Resume response:", response);
      console.log("Timer State: " + timerState.value);
      storeTimerState(data.value.name, response.name, "running", elapsed.value);
    } catch (error) {
      console.error("Error resuming time entry:", error);
    }
  }
}

async function completeTimer(
  maxDurationReached = false,
  isRestoration = false
) {
  if (isRestoration) return;
  if (timerState.value === "running") {
    console.log(
      "Hit on completeTimer and timerState.value running - current value: " +
        timerState.value
    );
    updateElapsed();
    timerState.value = "idle";
    clearInterval(timerInterval.value);

    try {
      const response = await createOrUpdateTimeEntry({
        ticket_id: data.value.name,
        agent: userId,
        name: currentEntryId.value,
        duration: elapsed.value,
        action: "complete",
        max_duration_reached: maxDurationReached,
      });
      console.log("Complete response:", response);
      console.log("Timer State: " + timerState.value);
      clearTimerState();
      elapsed.value = 0;
    } catch (error) {
      console.error("Failed to complete time entry:", error);
    }
  }
}

function createOrUpdateTimeEntry(data) {
  return new Promise((resolve, reject) => {
    fetch(
      "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.create_or_update_time_entry",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Frappe-CSRF-Token": window.csrf_token,
        },
        body: JSON.stringify(data),
      }
    )
      .then(handleApiResponse)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        console.log("Response data:", data.message);
        resolve(data.message);
      })
      .catch((error) => {
        console.error("Error creating or updating time entry:", error);
        reject(error);
      });
  });
}

function setupInterval() {
  clearInterval(timerInterval.value);
  timerInterval.value = setInterval(() => {
    updateElapsed();
  }, 1000);
}

function updateElapsed() {
  // If the timer is not running, immediately return without doing anything
  if (timerState.value !== "running") return;

  // Since the function continues, we know the timer is running
  const now = Date.now();
  if (startTime.value) {
    const timePassed = now - startTime.value;
    elapsed.value += timePassed;
    startTime.value = now; // Reset startTime for the next interval calculation

    if (elapsed.value >= maxDuration) {
      elapsed.value = maxDuration;
      completeTimer(true); // Automatically stop if max duration is reached
    }
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
  // Include startTime in the stored state if it's relevant for an ongoing timer
  const timerInfo = {
    ticketId: data.value.name,
    timeEntryId: currentEntryId.value,
    timerState: timerState.value,
    elapsed: elapsed.value,
    startTime: startTime.value, // Store startTime as well
  };
  localStorage.setItem("runningTimer", JSON.stringify(timerInfo));
}

function getStoredTimerState() {
  const runningTimer = localStorage.getItem("runningTimer");
  if (!runningTimer) return null;
  return JSON.parse(runningTimer);
}

async function initializeTimer() {
  const storedTimer = getStoredTimerState();
  console.log(
    "Stored timer state on initialization:",
    storedTimer ? JSON.stringify(storedTimer) : "No stored state"
  );

  if (storedTimer && storedTimer.ticketId === data.value.name) {
    timerState.value = storedTimer.timerState.toLowerCase();
    currentEntryId.value = storedTimer.timeEntryId;
    startTime.value = storedTimer.startTime
      ? new Date(storedTimer.startTime).getTime()
      : null;
    elapsed.value = storedTimer.elapsed;

    // For a paused timer, do not recalculate elapsed time upon page load
    if (timerState.value === "paused") {
      console.log("Timer was paused. Keeping elapsed time as is.");
    } else if (timerState.value === "running") {
      // Recalculate elapsed time only if the timer was running
      const now = Date.now();
      if (startTime.value) {
        const additionalElapsed = now - startTime.value;
        elapsed.value += additionalElapsed;
        // Update startTime to now to prevent further incorrect incrementation
        startTime.value = now;
      }
      setupInterval();
    }
  } else {
    console.log("No stored timer info found or does not match current ticket.");
    resetTimer();
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

async function checkTimeEntryStatus(timeEntryId) {
  return new Promise((resolve, reject) => {
    console.log(timeEntryId);
    fetch(
      `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.is_time_entry_running`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Frappe-CSRF-Token": window.csrf_token,
        },
        body: JSON.stringify({ time_entry_id: timeEntryId }),
      }
    )
      .then(handleApiResponse)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok.");
        }
        return response.json();
      })
      .then((data) => {
        resolve(data.message);
      })
      .catch((error) => {
        console.error("Error checking time entry status:", error);
        reject(error);
      });
  });
}

function handleApiResponse(response) {
  if (response.status === 401 || response.status === 403) {
    console.error("Unauthorized access, redirecting to login.");
    window.location.href = "/login";
  }
  return response;
}

window.addEventListener("beforeunload", () => {
  if (timerState.value === "running" || timerState.value === "paused") {
    console.log("beforeunload has a timerState.value of: " + timerState.value);
    storeTimerState(
      data.value.name,
      currentEntryId.value,
      timerState.value,
      elapsed.value
    );
  }
});
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
