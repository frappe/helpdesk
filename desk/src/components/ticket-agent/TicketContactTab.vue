<template>
  <!-- TODO: handle ellipsis -->
  <div>
    <!-- Contact -->
    <div v-if="!contact.loading">
      <div class="flex gap-3 items-center px-5 py-2.5">
        <Avatar
          :label="contact.data.name"
          :image="contact.data.image"
          size="2xl"
        />
        <p class="text-ink-gray-8 font-medium text-xl max-w-full truncate">
          {{ contact.data.name }}
        </p>
      </div>
      <div class="px-5 text-ink-gray-5 pb-2">
        <!-- Email Id -->
        <div class="flex gap-2 items-center p-1.5">
          <EmailIcon class="size-4" />
          <p class="text-p-sm text-ink-gray-6 hover:underline cursor-pointer">
            {{ contact.data.email_id }}
          </p>
          <CopyIcon
            class="size-4 cursor-pointer"
            @click="
              copyToClipboard(
                contact.data.email_id,
                `'${contact.data.email_id}' copied to clipboard`
              )
            "
          />
        </div>
        <!-- Mobile Number -->
        <div
          class="flex gap-2 items-center p-1.5"
          v-if="
            isCallingEnabled && (contact.data.mobile_no || contact.data.phone)
          "
        >
          <PhoneIcon class="size-4" />
          <p class="text-p-sm text-ink-gray-6 hover:underline cursor-pointer">
            {{ contact.data.mobile_no || contact.data.phone }}
          </p>
          <CopyIcon
            class="size-4 cursor-pointer"
            v-if="contact.data.mobile_no || contact.data.phone"
            @click="
              copyToClipboard(
                contact.data.mobile_no || contact.data.phone,
                `'${
                  contact.data.mobile_no || contact.data.phone
                }' copied to clipboard`
              )
            "
          />
        </div>
      </div>
    </div>

    <!-- Recent / Similar Tickets -->
    <template v-if="!recentSimilarTickets.loading">
      <div class="px-5 border-t pb-2.5" v-for="section in sections">
        <Section
          :key="section.label"
          :label="section.label"
          :hideLabel="section.hideLabel"
          :opened="section.opened"
        >
          <template #header="{ opened, hide, toggle }">
            <div class="flex gap-2.5 items-center py-[13px] justify-between">
              <Tooltip :text="section.tooltipMessage">
                <span
                  class="text-ink-gray-8 font-medium text-base cursor-pointer select-none"
                  @click="toggle"
                >
                  {{ section.label }}
                </span>
              </Tooltip>
              <LucideChevronDown
                class="size-4 text-ink-gray-6 cursor-pointer"
                :class="{ 'rotate-180': opened }"
                @click="toggle"
              />
            </div>
          </template>
          <ul>
            <li
              v-for="ticket in section.tickets"
              :key="ticket.name"
              class="py-2.5 cursor-pointer"
              @click="openTicket(ticket.name)"
            >
              <p class="text-base text-ink-gray-8 max-w-[60%] truncate">
                {{ ticket.subject }}
              </p>
              <div class="flex items-end justify-between">
                <p class="text-base text-ink-gray-5">
                  {{ formatDate(ticket.creation) + " &#183; " }}
                  <span class="transition duration-400 hover:underline">
                    {{ "#" + ticket.name }}
                  </span>
                </p>
                <p
                  class="px-1.5 py-[3px] text-sm rounded-sm max-w-[80px] text-center truncate h-5"
                  :class="getStatusColor(ticket.status)"
                >
                  {{ ticket.status }}
                </p>
              </div>
            </li>
          </ul>
        </Section>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useTelephonyStore } from "@/stores/telephony";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { RecentSimilarTicketsSymbol, TicketContactSymbol } from "@/types";
import { copyToClipboard } from "@/utils";
import dayjs from "dayjs";
import { Avatar, Tooltip } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, inject } from "vue";
import { CopyIcon } from "../icons";
import EmailIcon from "../icons/EmailIcon.vue";
import PhoneIcon from "../icons/PhoneIcon.vue";
import Section from "../Section.vue";
const telephonyStore = useTelephonyStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);

const contact = inject(TicketContactSymbol);
const recentSimilarTickets = inject(RecentSimilarTicketsSymbol);
const dateFormat = window.date_format;

const { getStatus, colorMap } = useTicketStatusStore();

function getStatusColor(status: string) {
  let { color } = getStatus(status);

  if (colorMap[color]) {
    return colorMap[color];
  } else {
    return colorMap["Default"];
  }
}

const sections = computed(() => {
  if (recentSimilarTickets.value.loading || !recentSimilarTickets.value.data) {
    return [];
  }
  const recentTickets = recentSimilarTickets.value?.data?.recent_tickets || [];
  const similarTickets =
    recentSimilarTickets.value?.data?.similar_tickets || [];
  const _sections = [];
  if (recentTickets.length) {
    _sections.push({
      label: "Recent Tickets",
      tooltipMessage: "Tickets recently raised by this contact/customer",
      hideLabel: false,
      opened: true,
      tickets: recentTickets,
    });
  }
  if (similarTickets.length) {
    _sections.push({
      label: "Similar Tickets",
      tooltipMessage: "Tickets with similar queries",
      hideLabel: false,
      opened: true,
      tickets: similarTickets,
    });
  }
  return _sections;
});

function formatDate(date: string) {
  return dayjs(date).format(dateFormat.toUpperCase());
}

function openTicket(name: string) {
  let url = window.location.origin + "/helpdesk/tickets/" + name;

  window.open(url, "_blank");
}
// v-if="(false && contact.data.mobile_no) || contact.data.phone"
</script>

<style scoped></style>
