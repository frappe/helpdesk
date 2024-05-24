<template>
  <Autocomplete
    ref="autocompleteRef"
    placeholder="Select an option"
    :options="options"
    :value="selection"
    @update:query="(q) => onUpdateQuery(q)"
    @change="(v) => (selection = v)"
  />
</template>

<script setup lang="ts">
import { Autocomplete } from "@/components";
import { createListResource } from "frappe-ui";
import { computed, ref, watchEffect } from "vue";
import { useAuthStore } from "@/stores/auth";

const props = defineProps({
  value: {
    type: String,
    required: false,
    default: "",
  },
  doctype: {
    type: String,
    required: true,
  },
  searchField: {
    type: String,
    required: false,
    default: "name",
  },
  labelField: {
    type: String,
    required: false,
    default: "name",
  },
  valueField: {
    type: String,
    required: false,
    default: "name",
  },
  pageLength: {
    type: Number,
    required: false,
    default: 1000,
  },
});

const r = createListResource({
  doctype: props.doctype,
  pageLength: props.pageLength,
  auto: true,
  fields: [props.labelField, props.searchField, props.valueField],
  filters: {
    [props.searchField]: ["like", `%${props.value}%`],
  },
  onSuccess: () => {
    selection.value = props.value
      ? options.value.find((o) => o.value === props.value)
      : null;
  },
});
const options = computed(
  () =>
    r.data?.map((result) => ({
      label: result[props.labelField],
      value: result[props.valueField],
    })) || []
);
const selection = ref(null);
const autocompleteRef = ref(null);
const authStore = useAuthStore();

function onUpdateQuery(query: string) {
  const parentTicketType = getParentTicketType();

  if (
    autocompleteRef.value &&
    props.doctype === "HD Ticket Type" &&
    parentTicketType
  ) {
    r.update({
      filters: {
        [props.searchField]: ["like", `%${query}%`],
        ["parent_ticket_type"]: ["=", parentTicketType],
      },
    });
  } else {
    r.update({
      filters: {
        [props.searchField]: ["like", `%${query}%`],
      },
    });
  }

  r.reload();
}

watchEffect(() => {
  if (autocompleteRef.value && props.doctype === "HD Ticket Type") {
    autocompleteRef.value?.$refs?.search?.$el?.addEventListener("focus", () => {
      let filters = {
        ["parent_ticket_type"]: ["=", getParentTicketType()],
      };
      UpdateQuery(filters);
    });
  } else if (autocompleteRef.value && props.doctype === "IO DP Master") {
    autocompleteRef.value?.$refs?.search?.$el?.addEventListener("focus", () => {
      let filters = {
        ["client_id"]: ["=", authStore.username],
      };
      UpdateQuery(filters);
    });
  }
});

function UpdateQuery(filters: any) {
  r.update({
    filters: filters,
  });

  r.reload();
}

function getParentTicketType() {
  const comboboxOptions = document.getElementById(
    "headlessui-combobox-options-4"
  );

  const selectedOption = comboboxOptions.querySelector(
    'li[aria-selected="true"]'
  );

  if (!selectedOption) {
    return;
  }

  const selectedValue = selectedOption.textContent.trim();
  return selectedValue;
}
</script>
