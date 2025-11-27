<template>
  <div
    class="h-full overflow-y-hidden flex flex-1 flex-col justify-between overflow-hidden max-h-full"
  >
    <div class="px-5 pb-4 flex flex-col">
      <!-- User avatar with buttons -->
      <TicketContact />
      <!-- Core Fields -->
      <div>
        <div
          v-for="(section, index) in coreFields"
          :key="index"
          :class="
            section.group ? 'flex gap-2 items-center w-full mb-3' : 'mb-3'
          "
        >
          <template v-for="field in section.fields">
            <Link
              v-if="field.visible"
              :key="field.fieldname"
              :ref="(el) => setFieldRef(field.fieldname, el)"
              class="form-control-core"
              :id="field.fieldname"
              :class="section.group ? 'flex-1' : 'w-full'"
              :page-length="10"
              :label="__(field.label)"
              :placeholder="__(field.placeholder)"
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

    <!-- Additional Fields -->
    <div class="border-t flex flex-col flex-1 h-full pb-3 overflow-y-hidden">
      <!-- TODO: Hack of 80 % for now, will refactor -->
      <div class="overflow-y-scroll max-h-[80%]">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import { parseField } from "@/composables/formCustomisation";
import { useNotifyTicketUpdate } from "@/composables/realtime";
import { useShortcut } from "@/composables/shortcuts";
import { getMeta } from "@/stores/meta";
import {
  ActivitiesSymbol,
  AssigneeSymbol,
  CustomizationSymbol,
  FieldValue,
  TicketSymbol,
} from "@/types";
import { computed, inject, ref } from "vue";
import TicketField from "../TicketField.vue";
import AssignTo from "./AssignTo.vue";
import TicketContact from "./TicketContact.vue";

const ticket = inject(TicketSymbol);
const assignees = inject(AssigneeSymbol);
const customizations = inject(CustomizationSymbol);
const activities = inject(ActivitiesSymbol);
const { getFields, getField } = getMeta("HD Ticket");
const { notifyTicketUpdate } = useNotifyTicketUpdate(ticket.value?.name);

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
  let _customFields = customFields.map((f) => {
    let fieldMeta = getField(f.fieldname);

    fieldMeta = parseField(fieldMeta, ticket.value.doc);
    // cant handle required depends on as we directly set the value in DB
    fieldMeta["required"] = fieldMeta.reqd || f.required;

    return getFieldInFormat(f, fieldMeta);
  });
  return _customFields;
});

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
