<template>
  <div class="flex gap-2 leading-5 items-center">
    <div class="w-[106px] shrink-0 truncate text-sm text-ink-gray-5">
      <Tooltip :text="__(field.label)">
        <span>{{ __(field.label) }}</span>
      </Tooltip>
      <span v-if="field.required" class="text-ink-red-6"> * </span>
    </div>
    <div
      class="-m-0.5 min-h-[28px] flex-1 items-center overflow-hidden p-0.5 text-base"
    >
      <component
        :is="component"
        :key="field.fieldname"
        :readonly="field.readonly"
        :disabled="field.disabled"
        class="form-control"
        :placeholder="field.placeholder || `Add ${field.label}`"
        :model-value="transValue"
        autocomplete="off"
        v-on="listeners"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Autocomplete } from "@/components";
import TicketPriority from "@/components/TicketPriority.vue";
import { APIOptions, Field, FieldValue } from "@/types";
import { parseApiOptions } from "@/utils";
import { Link } from "@framework/ui";
import {
  createResource,
  DatePicker,
  DateTimePicker,
  dayjs,
  FormControl,
  Tooltip,
} from "frappe-ui";
import { computed, h } from "vue";

interface P {
  field: Field;
  value: FieldValue;
}

interface R {
  fieldname: Field["fieldname"];
  value: FieldValue;
}

interface E {
  (event: "change", value: R);
}

const props = defineProps<P>();
const emit = defineEmits<E>();

const apiOptions = createResource({
  url: props.field.url_method,
  auto: !!props.field.url_method,
  transform: (data: APIOptions) => {
    return parseApiOptions(data);
  },
});

const textFields = ["Long Text", "Small Text", "Text", "Text Editor", "Data"];
const numberFields = ["Int", "Float", "Currency", "Percent"];

// Link doctypes whose records open on a helpdesk route. Presence here drives
// both the redirect affordance and where handleRedirect navigates; add a
// doctype -> route-segment entry to make another Link field redirectable.
const REDIRECT_ROUTES: Record<string, string> = {
  "HD Customer": "customers",
};

const component = computed(() => {
  if (props.field.url_method) {
    return h(Autocomplete, {
      options: apiOptions.data,
    });
  } else if (props.field.fieldtype === "Link" && props.field.options) {
    const linkProps = {
      doctype: props.field.options,
      redirectable: props.field.options in REDIRECT_ROUTES,
      class: "!w-full !bg-surface-base !border-transparent !text-base",
      onRedirect: handleRedirect,
    };
    // Priority shows its level icon before the selected value and each option.
    // The combobox reuses item-prefix for the control, so one slot drives both.
    if (props.field.options === "HD Ticket Priority") {
      return h(Link, linkProps, {
        "item-prefix": ({ item }: { item: { value: string } }) =>
          h(TicketPriority, { priority: item.value, iconOnly: true }),
      });
    }
    return h(Link, linkProps);
  } else if (props.field.fieldtype === "Select") {
    return h(Autocomplete, {
      options: props.field.options
        .split("\n")
        .map((o) => ({ label: o, value: o })),
    });
  } else if (props.field.fieldtype === "Check") {
    return h(Autocomplete, {
      options: [
        {
          label: "Yes",
          value: 1,
        },
        {
          label: "No",
          value: 0,
        },
      ],
    });
  } else if (textFields.includes(props.field.fieldtype)) {
    return h(FormControl, {
      type: "text",
    });
  } else if (props.field.fieldtype === "Datetime") {
    return h(DateTimePicker, {
      format: `${window.date_format.toUpperCase()} ${window.time_format}`,
    });
  } else if (props.field.fieldtype === "Date") {
    return h(DatePicker, {
      id: props.field.fieldname,
      format: window.date_format.toUpperCase(),
    });
  }
  // else if (props.field.fieldtype === "Duration") {
  //   // console.log("HERE TIME");
  //   return h(DurationField, { showSeconds: false });
  // }
  else {
    return h(FormControl);
  }
});

const listeners = computed(() => {
  const fieldtype = props.field.fieldtype;
  if ([...textFields, ...numberFields].includes(fieldtype)) {
    return {
      blur: (event: FocusEvent) =>
        emitUpdate(
          props.field.fieldname,
          (event.target as HTMLInputElement).value
        ),
    };
  }
  // The @framework/ui Link (Combobox) streams the typed query through
  // update:modelValue, so saving on it would persist half-typed text and
  // trip LinkValidationError. Persist only on a committed selection.
  if (fieldtype === "Link") {
    return {
      "update:selectedOption": (option: { value: string } | null) => {
        emitUpdate(props.field.fieldname, option?.value ?? "");
        // Keyboard commit leaves focus on the input; mouse commit already
        // blurs it. Blur here so both paths deselect the field consistently.
        (document.activeElement as HTMLElement | null)?.blur();
      },
      // Escape closes the listbox without committing and keeps focus on the
      // input; blur so it deselects the field like a commit does.
      keydown: (event: KeyboardEvent) => {
        if (event.key === "Escape") {
          (event.target as HTMLElement | null)?.blur();
        }
      },
    };
  }
  return {
    "update:model-value": (event: any) =>
      emitUpdate(
        props.field.fieldname,
        event?.value || event?.target?.value || event
      ),
  };
});

const transValue = computed(() => {
  const fieldtype = props.field.fieldtype;
  if (fieldtype === "Check") {
    return props.value ? "Yes" : "No";
  } else if (fieldtype === "Date") {
    if (!props.value) return props.value;
    return dayjs(props.value).format(window.date_format.toUpperCase());
  }
  // else if (fieldtype === "Duration") {
  //   if (!props.value) return null;
  // }
  return props.value;
});

function emitUpdate(fieldname: Field["fieldname"], value: FieldValue) {
  emit("change", { fieldname, value });
}

function handleRedirect(value: string) {
  const route = REDIRECT_ROUTES[props.field.options];
  if (!route) return;
  window.open(`${window.location.origin}/helpdesk/${route}/${value}`, "_blank");
}
</script>
<style scoped>
:deep(.form-control input:not([type="checkbox"])),
:deep(.form-control select),
:deep(.form-control textarea),
:deep(.form-control button) {
  border-color: transparent;
  background: var(--surface-base);
}

:deep(.form-control button) {
  gap: 0;
}
:deep(.form-control [type="checkbox"]) {
  margin-left: 9px;
  cursor: pointer;
}

:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
