<template>
  <!-- TODO: handle ellipsis -->
  <div>
    <!-- Contact -->
    <div v-if="showContact" class="px-5 pb-2">
      <div
        class="h-[250px] mt-2 bg-surface-white p-4 flex flex-col"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <LucideUser class="size-6 shrink-0 aspect-square text-ink-black" />
            <span
              class="font-['Poppins'] text-[16px] font-medium leading-[24px] text-ink-black"
            >
              Contact info
            </span>
          </div>
          <!-- <span
            class="font-['Poppins'] text-[12px] font-medium leading-[18px] text-ink-gray-6"
          >
            Edit
          </span> -->
        </div>

        <div class="mt-4 flex items-center gap-3">
          <div
            class="flex size-9 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-8"
          >
            <span class="font-['Poppins'] text-sm font-medium">
              {{ contactInitial }}
            </span>
          </div>
          <div class="min-w-0">
            <p
              class="font-['Poppins'] text-[14px] font-medium leading-[21px] text-ink-black truncate"
            >
              {{ contactName }}
            </p>
            <p
              class="font-['Poppins'] text-[12px] font-[250] leading-[18px] text-ink-gray-6 truncate"
            >
              {{ contactEmail }}
            </p>
          </div>
        </div>

        <div class="mt-4 flex flex-col gap-3">
          <div>
            <p
              class="font-['Poppins'] text-[12px] font-[250] leading-[18px] text-ink-gray-6"
            >
              Work Phone
            </p>
            <div class="mt-1 flex items-center gap-2">
              <p
                class="flex-1 truncate font-['Poppins'] text-[14px] font-[250] leading-[21px] text-ink-black"
              >
                {{ workPhone }}
              </p>
              <CopyIcon
                v-if="hasWorkPhone"
                class="size-4 cursor-pointer"
                @click="
                  copyToClipboard(
                    workPhoneValue,
                    `'${workPhoneValue}' copied to clipboard`
                  )
                "
              />
            </div>
          </div>
          <div>
            <p
              class="font-['Poppins'] text-[12px] font-[250] leading-[18px] text-ink-gray-6"
            >
              Phone Number
            </p>
            <div class="mt-1 flex items-center gap-2">
              <p
                class="flex-1 truncate font-['Poppins'] text-[14px] font-[250] leading-[21px] text-ink-black"
              >
                {{ phoneNumber }}
              </p>
              <CopyIcon
                v-if="hasPhoneNumber"
                class="size-4 cursor-pointer"
                @click="
                  copyToClipboard(
                    phoneNumberValue,
                    `'${phoneNumberValue}' copied to clipboard`
                  )
                "
              />
            </div>
          </div>
        </div>

        <!-- <span
          class="mt-auto font-['Poppins'] text-[12px] font-medium leading-[18px] text-ink-gray-6"
        >
          View More info
        </span> -->
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
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { RecentSimilarTicketsSymbol, TicketContactSymbol } from "@/types";
import { copyToClipboard } from "@/utils";
import dayjs from "dayjs";
import { Tooltip } from "frappe-ui";
import { computed, inject } from "vue";
import { CopyIcon } from "../icons";
import Section from "../Section.vue";
import LucideUser from "~icons/lucide/user";

const contact = inject(TicketContactSymbol);
const recentSimilarTickets = inject(RecentSimilarTicketsSymbol);
const dateFormat = window.date_format;

const { getStatus, colorMap } = useTicketStatusStore();
const contactData = computed(() => contact?.value?.data);
const contactNameValue = computed(() => contactData.value?.name?.trim());
const contactName = computed(() => contactNameValue.value || "Not available");
const contactEmailValue = computed(() => contactData.value?.email_id);
const contactEmail = computed(
  () => contactEmailValue.value || "Not available"
);
const workPhoneValue = computed(() => contactData.value?.mobile_no);
const workPhone = computed(() => workPhoneValue.value || "Not available");
const phoneNumberValue = computed(() => contactData.value?.phone);
const phoneNumber = computed(() => phoneNumberValue.value || "Not available");
const hasWorkPhone = computed(() => !!workPhoneValue.value);
const hasPhoneNumber = computed(() => !!phoneNumberValue.value);
const contactInitial = computed(() => {
  if (!contactNameValue.value) return "?";
  return contactNameValue.value[0].toUpperCase();
});
const showContact = computed(
  () => !!contact?.value && !contact.value.loading
);

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
</script>

<style scoped></style>
