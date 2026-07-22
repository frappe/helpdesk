<template>
  <div class="flex h-full flex-col">
    <!-- Contact header -->
    <div class="shrink-0 p-4 pb-3">
      <TicketContact />
    </div>

    <!-- SLA card, pinned with the contact header -->
    <TicketSLA class="shrink-0 px-4 pb-3.5" />

    <!-- Scrollable sections: Key Info + Ticket Info + Recent / Similar Tickets -->
    <div class="min-h-0 flex-1 divide-y-[1px] overflow-y-auto border-t">
      <!-- Key Info (core fields) -->
      <Section label="Key Info" v-model:opened="openedSections.keyInfo">
        <template #header="{ opened, toggle }">
          <div
            class="sticky top-0 z-10 flex cursor-pointer select-none items-center gap-1 bg-surface-base px-4 py-3.5"
            @click="toggle"
          >
            <span class="text-base-semibold text-ink-gray-8">
              {{ __("Key Info") }}
            </span>
            <LucideChevronRight
              class="size-3.5 text-ink-gray-6 transition-transform"
              :class="{ 'rotate-90': opened }"
            />
          </div>
        </template>
        <div class="mt-0.5 space-y-2.5 px-4 pb-4">
          <!-- Core fields -->
          <template v-for="field in coreFields">
            <TicketField
              v-if="field.visible"
              :key="field.fieldname"
              :ref="(el) => setFieldRef(field.fieldname, el)"
              :field="field"
              :value="field.value"
              @change="
                ({ fieldname, value }) =>
                  handleFieldUpdate(fieldname, value, true)
              "
            />
          </template>
          <!-- Assignee -->
          <div class="flex items-center gap-2 leading-5">
            <div class="w-[106px] shrink-0 truncate text-sm text-ink-gray-5">
              {{ __("Assignee") }}
            </div>
            <div
              class="-m-0.5 min-h-[28px] min-w-0 flex-1 items-center overflow-hidden p-0.5"
            >
              <AssignTo hide-label ghost />
            </div>
          </div>
          <!-- Tags -->
          <div class="flex items-start gap-2 leading-5">
            <div
              class="w-[106px] shrink-0 truncate pt-1 text-sm text-ink-gray-5"
            >
              {{ __("Labels") }}
            </div>
            <!-- 9px = field controls' 8px padding + 1px transparent border -->
            <div class="min-w-0 flex-1 py-0.5 ps-[9px]">
              <TicketTags />
            </div>
          </div>
        </div>
      </Section>

      <!-- Ticket Info (custom fields) -->
      <div v-if="Boolean(customFields.length)">
        <Section label="Ticket Info" v-model:opened="openedSections.ticketInfo">
          <template #header="{ opened, toggle }">
            <div
              class="sticky top-0 z-10 flex cursor-pointer select-none items-center gap-1 bg-surface-base px-4 py-3.5"
              @click="toggle"
            >
              <span class="text-base-semibold text-ink-gray-8">
                {{ __("Ticket Info") }}
              </span>
              <LucideChevronRight
                class="size-3.5 text-ink-gray-6 transition-transform"
                :class="{ 'rotate-90': opened }"
              />
            </div>
          </template>
          <div class="mt-0.5 space-y-2.5 px-4 pb-4">
            <template v-for="field in customFields">
              <TicketField
                v-if="field.visible"
                :key="field.fieldname"
                :field="field"
                :value="field.value"
                @change="
                  ({ fieldname, value }) => handleFieldUpdate(fieldname, value)
                "
              />
            </template>
          </div>
        </Section>
      </div>

      <!-- Recent / Similar Tickets -->
      <template v-if="showRecentSimilarTickets">
        <div v-for="section in sections" :key="section.label">
          <Section
            :label="section.label"
            :hideLabel="section.hideLabel"
            v-model:opened="openedSections[section.key]"
          >
            <template #header="{ opened, toggle }">
              <div
                class="sticky top-0 z-10 flex cursor-pointer select-none items-center gap-1 bg-surface-base px-4 py-3.5"
                @click="toggle"
              >
                <Tooltip :text="section.tooltipMessage">
                  <span class="text-base-semibold text-ink-gray-8">
                    {{ __(section.label) }}
                  </span>
                </Tooltip>
                <LucideChevronRight
                  class="size-3.5 text-ink-gray-6 transition-transform"
                  :class="{ 'rotate-90': opened }"
                />
              </div>
            </template>
            <ul class="divide-y divide-outline-gray-1 px-4 pb-4 pt-0">
              <li
                v-for="t in section.tickets"
                :key="t.name"
                @click="openTicket(t.name)"
              >
                <div
                  class="-mx-2 cursor-pointer rounded px-2 py-3 transition-colors hover:bg-surface-gray-2"
                >
                  <p class="font-base mb-2 truncate text-sm text-ink-gray-9">
                    {{ t.subject }}
                  </p>
                  <div class="flex items-center justify-between gap-2">
                    <p class="shrink-0 text-sm text-ink-gray-5">
                      {{ formatDate(t.creation as string) + " · " }}
                      <span class="">{{ "#" + t.name }}</span>
                    </p>
                    <span
                      class="font-base shrink-0 rounded-sm px-2 py-0.5 text-xs"
                      :class="getStatusColor(t.status as string)"
                    >
                      {{ t.status }}
                    </span>
                  </div>
                </div>
              </li>
            </ul>
          </Section>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { parseField } from "@/composables/formCustomisation";
import { useNotifyTicketUpdate } from "@/composables/realtime";
import { useShortcut } from "@/composables/shortcuts";
import { getMeta } from "@/stores/meta";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import {
  ActivitiesSymbol,
  AssigneeSymbol,
  CustomizationSymbol,
  FieldValue,
  RecentSimilarTicketsSymbol,
  TicketSymbol,
} from "@/types";
import { useStorage } from "@vueuse/core";
import { dayjs, Tooltip } from "frappe-ui";
import { computed, inject, ref } from "vue";
import LucideChevronRight from "~icons/lucide/chevron-right";
import Section from "../Section.vue";
import TicketField from "../TicketField.vue";
import AssignTo from "./AssignTo.vue";
import TicketContact from "./TicketContact.vue";
import TicketSLA from "./TicketSLA.vue";
import TicketTags from "./TicketTags.vue";

const ticket = inject(TicketSymbol)!;
const assignees = inject(AssigneeSymbol)!;
const customizations = inject(CustomizationSymbol)!;
const activities = inject(ActivitiesSymbol)!;
const recentSimilarTickets = inject(RecentSimilarTicketsSymbol)!;
const { getFields, getField } = getMeta("HD Ticket");
const { notifyTicketUpdate } = useNotifyTicketUpdate(ticket.value?.name);

const dateFormat = window.date_format;
const { getStatus, colorMap } = useTicketStatusStore();

const CORE_FIELDS = ["ticket_type", "priority", "customer", "agent_group"];

const coreFields = computed(() => {
  const fieldsMeta = getFields();
  if (!fieldsMeta || fieldsMeta.length === 0) {
    return [];
  }
  return CORE_FIELDS.map((fieldname) => {
    let field = getField(fieldname);
    if (!field) return null;
    field = parseField(field, ticket.value.doc);
    // cant handle required depends on as we directly set the value in DB on change
    field["required"] = field.reqd;
    const formatted = getFieldInFormat(field, field);
    formatted["visible"] = true;
    return formatted;
  }).filter(Boolean);
});

const customFields = computed(() => {
  const fieldsMeta = getFields();
  if (!fieldsMeta || fieldsMeta.length === 0) {
    return [];
  }

  if (!customizations.value.data || customizations.value.loading) return [];
  let customFields = customizations.value.data?.custom_fields || [];
  const excludedFields = [...CORE_FIELDS, "subject", "status"];
  customFields = customFields.filter(
    (f) => !excludedFields.includes(f.fieldname)
  );
  let _customFields = customFields
    .map((f) => {
      let fieldMeta = getField(f.fieldname);
      if (!fieldMeta) return null;

      fieldMeta = parseField(fieldMeta, ticket.value.doc);
      // cant handle required depends on as we directly set the value in DB
      fieldMeta["required"] = fieldMeta.reqd || f.required;

      return getFieldInFormat(f, fieldMeta);
    })
    .filter(Boolean);
  return _customFields;
});

const openedSections = useStorage(
  "openedSections",
  {
    keyInfo: true,
    ticketInfo: true,
    recentTickets: false,
    similarTickets: false,
  },
  localStorage,
  { mergeDefaults: true }
);

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
      key: "recentTickets" as const,
      label: "Recent Tickets",
      tooltipMessage: "Tickets recently raised by this contact/customer",
      hideLabel: false,
      tickets: recentTickets,
    });
  }
  if (similarTickets.length) {
    _sections.push({
      key: "similarTickets" as const,
      label: "Similar Tickets",
      tooltipMessage: "Tickets with similar queries",
      hideLabel: false,
      tickets: similarTickets,
    });
  }
  return _sections;
});

function getStatusColor(status: string) {
  const { color } = getStatus(status) ?? {};
  return colorMap[color] ?? colorMap["Default"];
}

function formatDate(date: string) {
  return dayjs(date).format(dateFormat.toUpperCase());
}

function openTicket(name: string) {
  let url = window.location.origin + "/helpdesk/tickets/" + name;
  window.open(url, "_blank");
}

function getFieldInFormat(fieldTemplate, fieldMeta) {
  return {
    label: fieldMeta?.label || fieldTemplate.fieldname,
    value: ticket.value.doc[fieldTemplate.fieldname],
    fieldtype: fieldMeta?.fieldtype,
    doctype: fieldMeta?.options || "",
    options: fieldMeta?.options || "",
    placeholder:
      fieldTemplate.placeholder ||
      `Set ${fieldMeta?.label || fieldTemplate.fieldname}...`,
    readonly: Boolean(fieldMeta.read_only),
    disabled: Boolean(fieldMeta.read_only),
    url_method: fieldTemplate.url_method || "",
    fieldname: fieldTemplate.fieldname,
    required: fieldTemplate.required || fieldMeta?.required || false,
    visible:
      fieldMeta.display_via_depends_on &&
      !fieldMeta.hidden &&
      (!!ticket.value.doc[fieldTemplate.fieldname] || !fieldMeta.read_only),
  };
}

const normalize = (v: string | FieldValue) =>
  v === null || v === undefined ? "" : v;

function handleFieldUpdate(
  fieldname: string,
  value: FieldValue,
  isCoreFieldUpdated = false
) {
  if (normalize(ticket.value.doc[fieldname]) == normalize(value)) return;
  if (isCoreFieldUpdated) {
    const label = getField(fieldname)?.label || fieldname;
    notifyTicketUpdate(label, value as string);
  }
  ticket.value.setValue.submit(
    { [fieldname]: value },
    {
      onSuccess: () => {
        // TODO: emit the event for notification to listeners
        if (fieldname === "agent_group") {
          assignees.value.reload();
        }
        activities.value.reload();
      },
    }

    //show error toast
  );
}

const fieldRefs = ref<Record<string, any>>({});

const setFieldRef = (fieldname: string, el: any) => {
  if (el) {
    fieldRefs.value[fieldname] = el;
  }
};

const showRecentSimilarTickets = computed(() => {
  return (
    !recentSimilarTickets.value.loading &&
    (recentSimilarTickets.value?.data?.recent_tickets?.length ||
      recentSimilarTickets.value?.data?.similar_tickets?.length)
  );
});

useShortcut("t", () => openFieldDropdown("ticket_type"));

useShortcut("p", () => openFieldDropdown("priority"));

useShortcut({ key: "t", shift: true }, () => openFieldDropdown("agent_group"));

// The @framework/ui Link renders a [role=combobox] input, not a button, and
// opens on ArrowDown from a focused input (a synthetic click won't open it).
function openFieldDropdown(fieldname: string) {
  const input = fieldRefs.value?.[fieldname]?.$el?.querySelector(
    '[role="combobox"]'
  ) as HTMLElement | null;
  if (!input) return;
  input.focus();
  input.dispatchEvent(
    new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true })
  );
}
</script>
