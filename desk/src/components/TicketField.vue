<template>
  <div class="flex gap-2 leading-5 items-center">
    <FieldLabel :label="field.label" :required="field.required" />
    <!-- p-1, not p-0.5: the Link pulls itself 2px left, so 2px of padding
         leaves its rounded corner shaved by overflow-hidden -->
    <div
      class="-m-1 min-h-[28px] flex-1 items-center overflow-hidden p-1 text-base"
    >
      <component
        :is="component"
        :key="field.fieldname"
        :readonly="field.readonly"
        :disabled="field.disabled"
        class="form-control"
        :placeholder="placeholder"
        :model-value="transValue"
        autocomplete="off"
        v-on="listeners"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Autocomplete } from "@/components";
import FieldLabel from "@/components/FieldLabel.vue";
import TicketPriority from "@/components/TicketPriority.vue";
import { APIOptions, Field, FieldValue } from "@/types";
import { parseApiOptions } from "@/utils";
import { Link } from "@framework/ui";
import {
  Combobox,
  createResource,
  DatePicker,
  DateTimePicker,
  dayjs,
  FormControl,
  Select,
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

// Link doctypes whose records open on a helpdesk route. Add an entry to make
// another Link field redirectable.
const REDIRECT_ROUTES: Record<string, string> = {
  "HD Customer": "customers",
};

// past this many options, the field gets a search box
const SEARCHABLE_FROM = 10;

// same overrides the Link fields carry: fill the row, stay flat on hover
const ghostControl = {
  variant: "ghost" as const,
  class: "!w-full !bg-surface-base",
};

type Option = { label: string; value: string | number };

const selectOptions = computed<Option[]>(() =>
  (props.field.fieldtype === "Select"
    ? props.field.options.split("\n")
    : []
  ).map((option) => ({ label: option, value: option }))
);

const isSearchableSelect = computed(
  () => selectOptions.value.length > SEARCHABLE_FROM
);

// the Combobox feeds one placeholder to both trigger and search box, so it
// gets none and its prefix slot carries the empty state instead
const emptyLabel = computed(
  () => props.field.placeholder || `Add ${props.field.label}`
);

const placeholder = computed(() =>
  isSearchableSelect.value ? "" : emptyLabel.value
);

function select(options: Option[]) {
  return h(Select, { ...ghostControl, options });
}

// trigger: "button" keeps the search inside the popover, so the row still
// reads as a value and not a text input
function combobox(options: Option[]) {
  return h(
    Combobox,
    {
      ...ghostControl,
      trigger: "button",
      options,
    },
    {
      prefix: () =>
        h("span", { class: "truncate text-ink-gray-4" }, emptyLabel.value),
    }
  );
}

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
    // item-prefix drives both the options and the control, so one slot puts
    // the level icon everywhere
    if (props.field.options === "HD Ticket Priority") {
      return h(Link, linkProps, {
        "item-prefix": ({ item }: { item: { value: string } }) =>
          h(TicketPriority, { priority: item.value, iconOnly: true }),
        // typing can drop the committed value from the options, so the
        // control falls back here; keep its icon until it changes
        prefix: () =>
          props.value
            ? h(TicketPriority, {
                priority: String(props.value),
                iconOnly: true,
              })
            : null,
      });
    }
    return h(Link, linkProps);
  } else if (props.field.fieldtype === "Select") {
    return isSearchableSelect.value
      ? combobox(selectOptions.value)
      : select(selectOptions.value);
  } else if (props.field.fieldtype === "Check") {
    return select([
      { label: "Yes", value: 1 },
      { label: "No", value: 0 },
    ]);
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

// the Link streams half-typed queries through update:modelValue, so commits
// wait for a real selection or for the picker to close still empty
let linkPickerOpen = false;
let linkModel: FieldValue = null;

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
  if (fieldtype === "Link") {
    return {
      "update:modelValue": (value: FieldValue) => {
        if (linkPickerOpen) linkModel = value;
        // only the clear (x) button nulls the model while the picker is closed
        else if (!value) emitUpdate(props.field.fieldname, "");
      },
      "update:selectedOption": (option: { value: string } | null) => {
        if (!option) return;
        emitUpdate(props.field.fieldname, option.value);
        // a mouse commit blurs the input already, a keyboard one doesn't
        (document.activeElement as HTMLElement | null)?.blur();
      },
      "update:open": (open: boolean) => {
        linkPickerOpen = open;
        if (open) linkModel = props.value ?? null;
        else if (!linkModel) emitUpdate(props.field.fieldname, "");
      },
      // Escape keeps focus on the input; blur so it deselects like a commit
      keydown: (event: KeyboardEvent) => {
        if (event.key === "Escape") {
          (event.target as HTMLElement | null)?.blur();
        }
      },
    };
  }
  // Camel, not hyphenated: Vue only recognises the camel form as a component's
  // declared emit. The hyphenated one falls through as an attr and the Combobox
  // re-binds it onto its search input, committing every keystroke
  return {
    "update:modelValue": (event: any) =>
      emitUpdate(
        props.field.fieldname,
        event?.value || event?.target?.value || event
      ),
  };
});

const transValue = computed(() => {
  const fieldtype = props.field.fieldtype;
  if (fieldtype === "Check") {
    // the Select matches on option value, so keep the stored 1 / 0
    return props.value ? 1 : 0;
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
  color: var(--ink-gray-7);
}

:deep(.form-control button) {
  gap: 0;
}

/* Select and Combobox reveal their chevron on hover like the Link fields.
   visibility, not display, so the row never reflows. */
:deep(button.form-control[data-slot="trigger"] .lucide-chevron-down) {
  visibility: hidden;
}

:deep(button.form-control[data-slot="trigger"]:hover .lucide-chevron-down),
:deep(button.form-control[data-slot="trigger"]:focus .lucide-chevron-down),
:deep(button.form-control[data-slot="trigger"][data-state="open"]
    .lucide-chevron-down) {
  visibility: visible;
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
