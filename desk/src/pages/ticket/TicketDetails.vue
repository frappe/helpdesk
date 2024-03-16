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
import { ref, computed, inject } from "vue";
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

// Methods
async function startTimer() {
  if (timerState.value !== "running") {
    timerState.value = "running";
    startTime.value = Date.now();
    clearInterval(timerInterval.value);

    // Optionally, create or update a time entry in the backend indicating the start
    try {
      const response = await createOrUpdateTimeEntry({
        ticket_id: data.value.name,
        agent: userId,
        action: "start",
        duration: null,
        name: currentEntryId.value, // This should be managed based on whether it's a new or existing time entry
        max_duration_reached: false, // Set based on logic in your application
      });
      currentEntryId.value = response.name;
      console.log("Timer State: " + timerState.value);

      timerInterval.value = setInterval(async () => {
        let elapsedSinceStart =
          Date.now() - startTime.value + (elapsed.value || 0);
        if (elapsedSinceStart >= maxDuration) {
          elapsedSinceStart = maxDuration;
          await completeTimer(true); // Pass true to indicate completion due to max duration reached
        }
      }, 1000);
    } catch (error) {
      console.error("Error starting time entry:", error);
    }
  }
}

async function pauseTimer() {
  if (timerState.value === "running") {
    clearInterval(timerInterval.value);
    timerState.value = "paused";
    elapsed.value += Date.now() - startTime.value;

    if (elapsed.value > maxDuration) {
      elapsed.value = maxDuration;
    }

    // Update the backend with the current duration and indicate pause
    try {
      const response = await createOrUpdateTimeEntry({
        ticket_id: data.value.name,
        agent: userId,
        name: currentEntryId.value,
        duration: elapsed.value,
        action: "pause",
        max_duration_reached: false,
      });
      console.log("Pause response:", response);
      console.log("Timer State: " + timerState.value);
    } catch (error) {
      console.error("Error pausing time entry:", error);
    }
  }
}

async function resumeTimer() {
  if (timerState.value === "paused") {
    timerState.value = "running";
    startTime.value = Date.now() - elapsed.value;
    timerInterval.value = setInterval(async () => {
      let currentElapsed = Date.now() - startTime.value + elapsed.value;
      if (currentElapsed >= maxDuration) {
        currentElapsed = maxDuration;
        await completeTimer(true); // Complete the timer if max duration is reached
      }
    }, 1000);

    // Update the backend with the current duration and indicate running
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
    } catch (error) {
      console.error("Error resuming time entry:", error);
    }
  }
}

async function completeTimer(maxDurationReached = false) {
  if (timerState.value !== "idle") {
    // Stop the timer
    clearInterval(timerInterval.value);
    // Calculate the final elapsed time
    const now = Date.now();
    let finalElapsed = now - startTime.value + elapsed.value;
    if (finalElapsed > maxDuration || maxDurationReached) {
      finalElapsed = maxDuration;
    }
    // Update the elapsed time
    elapsed.value = finalElapsed;
    // Update the timer state
    timerState.value = "idle";

    // Send an update to the backend to mark the timer as completed
    try {
      const response = await createOrUpdateTimeEntry({
        ticket_id: data.value.name,
        agent: userId,
        name: currentEntryId.value, // Use the ID of the current time entry
        duration: elapsed.value, // Send the total elapsed time in milliseconds
        action: "complete",
        max_duration_reached: maxDurationReached, // Indicate if the timer was auto-completed due to max duration reached
      });
      console.log("Complete response:", response);
      console.log("Timer State: " + timerState.value);
      // Reset the elapsed time for the next timer session
      elapsed.value = 0;
    } catch (error) {
      console.error("Failed to complete time entry:", error);
    }
  }
}

function createOrUpdateTimeEntry(data) {
  return new Promise((resolve, reject) => {
    fetch("/api/method/itsm.itsm.create_or_update_time_entry", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Frappe-CSRF-Token": window.csrf_token,
      },
      body: JSON.stringify(data),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        console.log("Response data:", data.message);
        console.log("Response data:", data.message.name);
        resolve(data.message);
      })
      .catch((error) => {
        console.error("Error creating or updating time entry:", error);
        reject(error);
      });
  });
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
