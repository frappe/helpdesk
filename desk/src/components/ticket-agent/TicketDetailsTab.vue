<template>
  <div class="flex h-full flex-col">
    <div class="shrink-0 px-5 pb-4 flex flex-col">
      <!-- User avatar with buttons -->
      <TicketContact />
      <!-- Core Fields -->
      <div>
        <div
          v-for="(section, index) in coreFields"
          :key="index"
          :class="
            section.group ? 'flex gap-2 items-start max-w-full mb-3' : 'mb-3'
          "
        >
          <template v-for="field in section.fields">
            <Link
              v-if="field.visible"
              :key="field.fieldname"
              :ref="(el) => setFieldRef(field.fieldname, el)"
              class="form-control-core"
              :id="field.fieldname"
              :class="section.group ? 'flex-1 min-w-0' : 'w-full'"
              :page-length="10"
              :label="field.label"
              :placeholder="field.placeholder"
              :doctype="field.doctype"
              :modelValue="field.value"
              :required="field.required"
              @update:model-value="
              (val:string) => handleFieldUpdate(field.fieldname, val,true)
            "
            />
          </template>
        </div>

        <!-- Assignee component -->
        <AssignTo />
      </div>
    </div>

    <!-- Scrollable sections: Ticket Info + Recent / Similar Tickets -->
    <div class="border-t flex-1 min-h-0 overflow-y-auto divide-y-[1px]">
      <!-- Ticket Info (custom fields) -->
      <div v-if="Boolean(customFields.length)">
        <Section label="Ticket Info" :opened="true">
          <template #header="{ opened, toggle }">
            <div
              class="flex gap-2.5 items-center justify-between sticky top-0 bg-surface-white z-10 px-5 py-4 cursor-pointer"
              @click="toggle"
            >
              <span class="text-ink-gray-8 font-medium text-base select-none">
                Ticket Info
              </span>
              <LucideChevronRight
                class="size-4 text-ink-gray-6"
                :class="{ 'rotate-90': opened }"
              />
            </div>
          </template>
          <div class="space-y-1.5 px-5 last:mb-3">
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
      <template v-if="!recentSimilarTickets.loading">
        <div v-for="section in sections" :key="section.label">
          <Section
            :label="section.label"
            :hideLabel="section.hideLabel"
            :opened="section.opened"
          >
            <template #header="{ opened, toggle }">
              <div
                class="flex gap-2.5 items-center justify-between sticky top-0 bg-surface-white z-10 px-5 py-4 cursor-pointer"
                @click="toggle"
              >
                <Tooltip :text="section.tooltipMessage">
                  <span
                    class="text-ink-gray-8 font-medium text-base select-none"
                  >
                    {{ section.label }}
                  </span>
                </Tooltip>
                <LucideChevronRight
                  class="size-4 text-ink-gray-6"
                  :class="{ 'rotate-90': opened }"
                />
              </div>
            </template>
            <ul class="pb-3 pt-0 px-5">
              <li
                v-for="t in section.tickets"
                :key="t.name"
                class="py-2.5 cursor-pointer"
                @click="openTicket(t.name)"
              >
                <p class="text-base text-ink-gray-8 max-w-[60%] truncate">
                  {{ t.subject }}
                </p>
                <div class="flex items-end justify-between">
                  <p class="text-base text-ink-gray-5">
                    {{ formatDate(t.creation) + " · " }}
                    <span class="transition duration-400 hover:underline">
                      {{ "#" + t.name }}
                    </span>
                  </p>
                  <p
                    class="px-1.5 py-[3px] text-sm rounded-sm max-w-[80px] text-center truncate h-5"
                    :class="getStatusColor(t.status)"
                  >
                    {{ t.status }}
                  </p>
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
import { Link } from "@/components";
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
import dayjs from "dayjs";
import { Tooltip } from "frappe-ui";
import { computed, inject, ref } from "vue";
import LucideChevronRight from "~icons/lucide/chevron-right";
import Section from "../Section.vue";
import TicketField from "../TicketField.vue";
import AssignTo from "./AssignTo.vue";
import TicketContact from "./TicketContact.vue";

const ticket = inject(TicketSymbol);
const assignees = inject(AssigneeSymbol);
const customizations = inject(CustomizationSymbol);
const activities = inject(ActivitiesSymbol);
const recentSimilarTickets = inject(RecentSimilarTicketsSymbol)!;
const { getFields, getField } = getMeta("HD Ticket");
const { notifyTicketUpdate } = useNotifyTicketUpdate(ticket.value?.name);

const dateFormat = window.date_format;
const { getStatus, colorMap } = useTicketStatusStore();

// ticket_type, priority, customer, agent_group
const coreFields = computed(() => {
  // TODO: to confirm whether customizations should apply to core fields as well
  const fieldsMeta = getFields();
  if (!fieldsMeta || fieldsMeta.length === 0) {
    return [];
  }
  const _coreFields = [
    { group: true, fields: [getField("ticket_type"), getField("priority")] },
    { group: false, fields: [getField("customer")] },
    { group: true, fields: [getField("agent_group")] },
  ];

  _coreFields.forEach((section) => {
    section.fields = section.fields.map((f) => {
      f = parseField(f, ticket.value.doc);

      // cant handle required depends on as we directly set the value in DB on change
      f["required"] = f.reqd;
      f["ref"] = f.fieldname;

      f = getFieldInFormat(f, f);
      f["visible"] = true;
      return f;
    });
  });
  return _coreFields;
});

const customFields = computed(() => {
  const fieldsMeta = getFields();
  if (!fieldsMeta || fieldsMeta.length === 0) {
    return [];
  }

  if (!customizations.value.data || customizations.value.loading) return [];
  let customFields = customizations.value.data?.custom_fields || [];
  const _coreFields = [
    "ticket_type",
    "priority",
    "customer",
    "agent_group",
    "subject",
    "status",
  ];
  customFields = customFields.filter((f) => !_coreFields.includes(f.fieldname));
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

function getStatusColor(status: string) {
  let { color } = getStatus(status);
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
      `Enter ${fieldMeta?.label || fieldTemplate.fieldname}`,
    readonly: Boolean(fieldMeta.read_only),
    disabled: Boolean(fieldMeta.read_only),
    url_method: fieldTemplate.url_method || "",
    fieldname: fieldTemplate.fieldname,
    required: fieldTemplate.required || fieldMeta?.required || false,
    visible: fieldMeta.display_via_depends_on && !fieldMeta.hidden,
  };
}

function handleFieldUpdate(
  fieldname: string,
  value: FieldValue,
  isCoreFieldUpdated = false
) {
  if (ticket.value.doc[fieldname] == value) return;
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

useShortcut("t", () => {
  fieldRefs.value?.ticket_type?.$el?.querySelector("button")?.click();
});

useShortcut("p", () => {
  fieldRefs.value?.priority?.$el?.querySelector("button")?.click();
});

useShortcut({ key: "t", shift: true }, () => {
  fieldRefs.value?.agent_group?.$el?.querySelector("button")?.click();
});
</script>

<style scoped>
:deep(.form-control-core button) {
  @apply text-base rounded h-7 py-1.5 border border-outline-gray-2 bg-surface-white placeholder-ink-gray-4 hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-0 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark];
}
:deep(.form-control-core button > div) {
  @apply truncate;
}

:deep(.form-control-core div) {
  width: 100%;
  display: flex;
}
</style>
