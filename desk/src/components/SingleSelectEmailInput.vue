<template>
  <div>
    <Combobox v-model="selectedValue" nullable>
      <Popover v-model:show="showOptions" class="w-full">
        <template #target="{ togglePopover }">
          <ComboboxInput
            ref="search"
            class="search-input form-input w-full border-none bg-white hover:bg-white focus:border-none focus:!shadow-none focus-visible:!ring-0"
            type="text"
            :value="displayValue"
            autocomplete="off"
            @change="
              (e) => {
                query = e.target.value;
                showOptions = true;
              }
            "
            @focus="() => togglePopover()"
            readonly
          />
        </template>
        <template #body="{ isOpen }">
          <div v-show="isOpen">
            <div class="mt-1 rounded-lg bg-white py-1 text-base shadow-2xl">
              <ComboboxOptions
                class="my-1 max-h-[12rem] overflow-y-auto px-1.5"
                static
              >
                <div
                  v-if="!options.length"
                  class="flex gap-2 rounded px-2 py-1 text-base text-gray-500"
                >
                  No email accounts found
                </div>
                <ComboboxOption
                  v-for="option in options"
                  :key="option.value"
                  v-slot="{ active }"
                  :value="option"
                >
                  <li
                    :class="[
                      'flex cursor-pointer items-center rounded px-2 py-1 text-base',
                      { 'bg-gray-100': active },
                    ]"
                  >
                    <div class="flex flex-col gap-1 p-1 text-gray-800">
                      <div class="text-base font-medium">
                        {{ option.label }}
                      </div>
                    </div>
                  </li>
                </ComboboxOption>
              </ComboboxOptions>
            </div>
          </div>
        </template>
      </Popover>
    </Combobox>
  </div>
</template>

<script setup lang="ts">
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from "@headlessui/vue";
import { Popover, createResource } from "frappe-ui";
import { ref, computed, watch } from "vue";

const props = defineProps({
  placeholder: {
    type: String,
    default: "Select email account",
  },
});

const modelValue = defineModel<string | null>();

const search = ref(null);
const query = ref("");
const showOptions = ref(false);

const emailAccounts = createResource({
  url: "helpdesk.api.settings.email.get_outgoing_email_accounts",
  auto: true,
  cache: "user-outgoing-email-accounts",
});

const options = computed(() => {
  if (!emailAccounts.data) return [];

  // Filter options based on query
  if (query.value) {
    return emailAccounts.data.filter((option: any) =>
      option.label.toLowerCase().includes(query.value.toLowerCase())
    );
  }
  return emailAccounts.data;
});

const displayValue = computed(() => {
  if (!modelValue.value) return "";
  const selected = emailAccounts.data?.find(
    (opt: any) => opt.value === modelValue.value
  );
  return selected ? selected.label : "";
});

const selectedValue = computed({
  get: () => {
    if (!modelValue.value) return null;
    return emailAccounts.data?.find(
      (opt: any) => opt.value === modelValue.value
    );
  },
  set: (val: any) => {
    query.value = "";
    if (val) {
      showOptions.value = false;
      modelValue.value = val.value;
    } else {
      modelValue.value = null;
    }
  },
});

// Auto-select first email account if none selected and accounts are loaded
watch(
  () => emailAccounts.data,
  (accounts: any) => {
    if (accounts && accounts.length > 0 && !modelValue.value) {
      modelValue.value = accounts[0].value;
    }
  },
  { immediate: true }
);

function setFocus() {
  search.value?.$el?.focus();
}

defineExpose({ setFocus });
</script>

