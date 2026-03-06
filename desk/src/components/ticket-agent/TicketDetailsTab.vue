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
              :label="field.label"
              :placeholder="field.placeholder"
              :doctype="field.doctype"
              :modelValue="field.value"
              :required="field.required"
              :filters="field.filters"
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
import {
  handleLinkFieldUpdate,
  handleSelectFieldUpdate,
  parseField,
  setupCustomizations,
} from "@/composables/formCustomisation";
import { useNotifyTicketUpdate } from "@/composables/realtime";
import { useShortcut } from "@/composables/shortcuts";
import { globalStore } from "@/stores/globalStore";
import { getMeta } from "@/stores/meta";
import {
  ActivitiesSymbol,
  AssigneeSymbol,
  CustomizationSymbol,
  FieldValue,
  TicketSymbol,
} from "@/types";
import { call, toast } from "frappe-ui";
import { computed, inject, reactive, ref, watchEffect } from "vue";
import { useRouter } from "vue-router";
import TicketField from "../TicketField.vue";
import AssignTo from "./AssignTo.vue";
import TicketContact from "./TicketContact.vue";

const ticket = inject(TicketSymbol);
const assignees = inject(AssigneeSymbol);
const customizations = inject(CustomizationSymbol);
const activities = inject(ActivitiesSymbol);
const { getFields, getField } = getMeta("HD Ticket");
const { notifyTicketUpdate } = useNotifyTicketUpdate(ticket.value?.name);
const router = useRouter();
const { $dialog } = globalStore();

const fieldOverrides = reactive<Record<string, Record<string, any>>>({});
const snapshotsCache = new Map<
  string,
  { fieldname: string; options: string; link_filters: string }
>();

const applyFilters = (
  fieldname: string,
  filters: string[] | null = null
): void => {
  const fieldMeta = getField(fieldname);
  if (!fieldMeta) return;
  const fieldCopy = { ...fieldMeta };

  const snapshot = snapshotsCache.get(fieldname);
  const oldFieldData = snapshot || {
    fieldname,
    options: fieldCopy.options || "",
    link_filters: fieldCopy.link_filters || "",
  };

  if (fieldCopy.fieldtype === "Select") {
    handleSelectFieldUpdate(
      fieldCopy,
      fieldname,
      filters,
      ticket.value.doc,
      [oldFieldData],
      false // shouldReset: false for edit mode
    );
    fieldOverrides[fieldname] = {
      options: fieldCopy.options,
      disabled: !filters?.length,
    };
  } else if (fieldCopy.fieldtype === "Link") {
    handleLinkFieldUpdate(
      fieldCopy,
      fieldname,
      filters,
      ticket.value.doc,
      [oldFieldData],
      false // shouldReset: false for edit mode
    );
    fieldOverrides[fieldname] = {
      link_filters: fieldCopy.link_filters,
      disabled: !filters?.length,
    };
  }
};

function updateField(fieldname: string, value: string, callback = () => {}) {
  ticket.value.setValue.submit({ [fieldname]: value });
  callback();
}

const customizationCtx = computed(() => ({
  doc: ticket?.value?.doc,
  call,
  router,
  toast,
  $dialog,
  updateField,
  createToast: toast.create,
  applyFilters,
}));

const localCustomizationData = ref<Record<string, any> | null>(null);

watchEffect(async () => {
  if (!customizations.value?.data || !ticket.value?.doc) return;

  localCustomizationData.value = { ...customizations.value.data };

  await setupCustomizations(
    localCustomizationData.value,
    customizationCtx.value
  );

  const onChangeHandlers = localCustomizationData.value?._customOnChange;
  if (!onChangeHandlers) return;

  Object.entries(onChangeHandlers).forEach(([fieldname, handlers]) => {
    const currentValue = ticket.value.doc[fieldname];
    if (currentValue == null || currentValue === "") return;

    const fieldtype = getField(fieldname)?.fieldtype;
    (handlers as Function[]).forEach((fn) => fn(currentValue, fieldtype));
  });
});

const customOnChange = computed(
  () => localCustomizationData.value?._customOnChange
);

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

      if (!snapshotsCache.has(f.fieldname)) {
        snapshotsCache.set(f.fieldname, {
          fieldname: f.fieldname,
          options: f.options || "",
          link_filters: f.link_filters || "",
        });
      }

      // cant handle required depends on as we directly set the value in DB on change
      f["required"] = f.reqd;
      f["ref"] = f.fieldname;

      f = getFieldInFormat(f, f);
      f["visible"] = true;

      // Apply fieldOverrides from applyFilters (field dependency)
      const overrides = fieldOverrides[f.fieldname];
      if (overrides) {
        f = {
          ...f,
          ...overrides,
          filters: overrides.link_filters
            ? JSON.parse(overrides.link_filters)
            : f.filters,
        };
      }

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
  let customFieldsList = customizations.value.data?.custom_fields || [];
  const _coreFields = [
    "ticket_type",
    "priority",
    "customer",
    "agent_group",
    "subject",
    "status",
  ];
  customFieldsList = customFieldsList.filter(
    (f) => !_coreFields.includes(f.fieldname)
  );

  // Only clear non-core snapshots so core field snapshots persist
  for (const key of snapshotsCache.keys()) {
    if (!_coreFields.includes(key)) {
      snapshotsCache.delete(key);
    }
  }

  return customFieldsList
    .map((f) => {
      const fieldMeta = parseField(getField(f.fieldname), ticket.value.doc);
      if (!fieldMeta) return null;

      snapshotsCache.set(f.fieldname, {
        fieldname: f.fieldname,
        options: fieldMeta.options || "",
        link_filters: fieldMeta.link_filters || "",
      });

      const formatted = getFieldInFormat(f, {
        ...fieldMeta,
        required: fieldMeta.reqd || f.required,
      });
      const overrides = fieldOverrides[f.fieldname];

      return overrides
        ? {
            ...formatted,
            ...overrides,
            filters: overrides.link_filters
              ? JSON.parse(overrides.link_filters)
              : formatted.filters,
          }
        : formatted;
    })
    .filter(Boolean);
});

function getFieldInFormat(fieldTemplate, fieldMeta) {
  return {
    label: fieldMeta?.label || fieldTemplate.fieldname,
    value: ticket.value.doc[fieldTemplate.fieldname],
    fieldtype: fieldMeta?.fieldtype,
    doctype: fieldMeta?.options || "",
    options: fieldMeta?.options || "",
    link_filters: fieldMeta?.link_filters || "",
    filters: fieldMeta?.link_filters
      ? JSON.parse(fieldMeta.link_filters)
      : undefined,
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
  const oldValue = ticket.value.doc[fieldname];
  if (oldValue === value) return;

  ticket.value.doc[fieldname] = value;
  customOnChange.value?.[fieldname]?.forEach((fn: Function) =>
    fn(value, getField(fieldname)?.fieldtype)
  );

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
