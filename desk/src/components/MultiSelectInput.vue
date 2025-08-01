<template>
  <div>
    <div class="flex flex-wrap gap-1">
      <Button
        v-for="value in values"
        ref="emails"
        :key="value"
        :label="value"
        theme="gray"
        variant="subtle"
        class="rounded-full"
        @keydown.delete.capture.stop="removeLastValue"
      >
        <template #suffix>
          <FeatherIcon
            class="h-3.5"
            name="x"
            @click.stop="removeValue(value)"
          />
        </template>
      </Button>
      <div class="flex-1">
        <Combobox v-model="selectedValue" nullable>
          <Popover v-model:show="showOptions" class="w-full">
            <template #target="{ togglePopover }">
              <ComboboxInput
                ref="search"
                class="search-input form-input w-full border-none bg-white hover:bg-white focus:border-none focus:!shadow-none focus-visible:!ring-0"
                type="text"
                :value="query"
                autocomplete="off"
                @change="
                  (e) => {
                    query = e.target.value;
                    showOptions = true;
                  }
                "
                @focus="() => togglePopover()"
                @keydown.delete.capture.stop="removeLastValue"
              />
            </template>
            <template #body="{ isOpen }">
              <div v-show="isOpen">
                <div class="mt-1 rounded-lg bg-white py-1 text-base shadow-2xl">
                  <ComboboxOptions
                    class="my-1 max-h-[12rem] overflow-y-auto px-1.5"
                    static
                  >
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
                        <UserAvatar
                          class="mr-2"
                          :name="option.value"
                          size="lg"
                        />
                        <div class="flex flex-col gap-1 p-1 text-gray-800">
                          <div class="text-base font-medium">
                            {{ option.label }}
                          </div>
                          <div class="text-sm text-gray-600">
                            {{ option.value }}
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
    </div>
    <ErrorMessage v-if="error" class="mt-2 pl-2" :message="error" />
  </div>
</template>

<script setup lang="ts">
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from "@headlessui/vue";
import { UserAvatar } from "@/components/";
import { Popover, createResource } from "frappe-ui";
import { ref, computed, nextTick } from "vue";
import { watchDebounced } from "@vueuse/core";

const props = defineProps({
  validate: {
    type: Function,
    default: null,
  },
  errorMessage: {
    type: Function,
    default: (value) => `${value} is an Invalid value`,
  },
});

const values = defineModel();

const emails = ref([]);
const search = ref(null);
const error = ref(null);
const query = ref("");
const text = ref("");
const showOptions = ref(false);

const selectedValue = computed({
  get: () => query.value || "",
  set: (val) => {
    query.value = "";
    if (val) {
      showOptions.value = false;
    }
    val?.value && addValue(val.value);
  },
});

watchDebounced(
  query,
  (val) => {
    val = val || "";
    if (text.value === val) return;
    text.value = val;
    reload(val);
  },
  { debounce: 300, immediate: true }
);

const filterOptions = createResource({
  url: "helpdesk.api.contact.search_contacts",
  method: "GET",
  cache: ["Contact", text.value],
  params: {
    txt: text.value,
  },
  transform: (data: Record<"full_name" | "name" | "email_id", string>[]) => {
    return data.map(({ full_name, email_id, name }) => ({
      label: full_name || name || email_id,
      value: email_id,
    }));
  },
});

const options = computed(() => {
  let searchedContacts = filterOptions.data || [];
  if (!searchedContacts.length && query.value) {
    searchedContacts.push({
      label: query.value,
      value: query.value,
    });
  }
  return searchedContacts;
});

function reload(val) {
  filterOptions.update({
    params: {
      txt: val,
    },
  });
  filterOptions.reload();
}

const addValue = (value) => {
  error.value = null;
  if (value) {
    const splitValues = value.split(",");
    splitValues.forEach((value) => {
      value = value.trim();
      if (value) {
        // check if value is not already in the values array
        if (!values.value?.includes(value)) {
          // check if value is valid
          if (value && props.validate && !props.validate(value)) {
            error.value = props.errorMessage(value);
            return;
          }
          // add value to values array
          if (!values.value) {
            values.value = [value];
          } else {
            values.value.push(value);
          }
          value = value.replace(value, "");
        }
      }
    });
    !error.value && (value = "");
  }
};

const removeValue = (value) => {
  values.value = values.value.filter((v) => v !== value);
};

const removeLastValue = () => {
  if (query.value) return;

  let emailRef = emails.value[emails.value.length - 1]?.$el;
  if (document.activeElement === emailRef) {
    values.value.pop();
    nextTick(() => {
      if (values.value.length) {
        emailRef = emails.value[emails.value.length - 1].$el;
        emailRef?.focus();
      } else {
        setFocus();
      }
    });
  } else {
    emailRef?.focus();
  }
};

function setFocus() {
  search.value.$el.focus();
}

defineExpose({ setFocus });
</script>
