<template>
  <div class="space-y-2 border-b px-6 py-3">
    <div class="flex items-center gap-3">
      <IconChevronLeft
        class="h-4 w-4 cursor-pointer text-gray-700"
        @click="goBack"
      />
      <div class="line-clamp-1 text-xl font-medium text-gray-900">
        {{ ticket.doc.subject }}
      </div>
    </div>
    <div class="ml-7 flex items-center gap-1 text-base text-gray-600">
      <Tooltip :text="viaCustomerPortal ? textCustomerPortal : textEmail">
        <component
          :is="viaCustomerPortal ? IconGlobe : IconAtSign"
          class="h-4 w-4"
        />
      </Tooltip>
      <IconDot />
      <div class="cursor-copy" @click="copyId"># {{ ticket.doc.name }}</div>
      <IconDot />
      <Tooltip :text="dateLong"> Last modified {{ dateShort }} </Tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Tooltip } from "frappe-ui";
import { useClipboard } from "@vueuse/core";
import dayjs from "dayjs";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { useTicketStore } from "./data";
import { createToast } from "@/utils/toasts";
import IconAtSign from "~icons/lucide/at-sign";
import IconChevronLeft from "~icons/lucide/chevron-left";
import IconDot from "~icons/lucide/dot";
import IconGlobe from "~icons/lucide/globe";

const { copy } = useClipboard();
const router = useRouter();
const { ticket } = useTicketStore();

const date = computed(() => dayjs(ticket.doc.modified).tz(dayjs.tz.guess()));
const dateShort = computed(() => date.value.fromNow());
const dateLong = computed(() => date.value.format("dddd, MMMM D, YYYY h:mm A"));
const viaCustomerPortal = computed(() => ticket.doc.via_customer_portal);
const textEmail = "Created via email";
const textCustomerPortal = "Created via customer portal";

async function copyId() {
  await copy(ticket.doc.name);

  createToast({
    title: "Copied to clipboard",
    icon: "check",
    iconClasses: "text-green-600",
  });
}

function goBack() {
  function fallback() {
    router.push({ name: AGENT_PORTAL_TICKET_LIST });
  }

  const previousPage = window.history.state.back;
  if (!previousPage) fallback();

  const route = router.resolve({ path: window.history.state.back });

  if (route.name === AGENT_PORTAL_TICKET_LIST) router.back();
  else fallback();
}
</script>
