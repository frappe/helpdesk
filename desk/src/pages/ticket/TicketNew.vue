<template>
  <div class="flex flex-col overflow-y-auto">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <CustomActions v-if="customActions.length" :actions="customActions" />
      </template>
    </LayoutHeader>
    <div class="mx-auto w-full max-w-4xl px-5 pt-6">
      <NewTicketForm
        :template="templateId || 'Default'"
        :initial-subject="String(route.query.subject ?? '')"
        is-agent
        :date-format="dateFormat"
        :time-format="timeFormat"
        :dialog="$dialog"
        @actions="customActions = $event"
        @created="openTicket"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader } from "@/components";
// The portal's own; Studio only finds custom components under studio/.
import CustomActions from "../../../../studio/helpdesk/components/header/CustomActions.vue";
import NewTicketForm from "../../../../studio/helpdesk/components/ticket/NewTicketForm.vue";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { useOnboarding } from "@framework/ui";
import { Breadcrumbs, usePageMeta } from "frappe-ui";
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

defineProps<{ templateId?: string }>();

const route = useRoute();
const router = useRouter();
const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};
const { isManager, userId: userID } = useAuthStore();
const customActions = ref([]);
const { $dialog } = globalStore();
const dateFormat = window.date_format?.toUpperCase();
const timeFormat = window.time_format;

function openTicket(ticket: { name: string }) {
  router.push({ name: "TicketAgent", params: { ticketId: ticket.name } });
  if (isManager) {
    updateOnboardingStep?.("create_first_ticket", true, false, () =>
      localStorage.setItem("firstTicket", ticket.name)
    );
  }
}

const breadcrumbs = [
  { label: __("Tickets"), route: { name: "TicketsAgent" } },
  { label: __("New Ticket"), route: { name: "TicketAgentNew" } },
];

usePageMeta(() => ({ title: __("New Ticket") }));

onMounted(() => capture("new_ticket_page", { data: { user: userID } }));
</script>
