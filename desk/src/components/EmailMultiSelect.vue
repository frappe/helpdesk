<template>
  <div>
    <div class="flex flex-wrap gap-1">
      <Button
        ref="emails"
        v-for="value in values"
        :key="value"
        :label="value"
        theme="gray"
        variant="subtle"
        :class="{
          'rounded bg-surface-white hover:!bg-surface-gray-1 focus-visible:ring-outline-gray-4':
            variant === 'subtle',
        }"
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
        <ComboboxRoot
          :model-value="tempSelection"
          :open="showOptions"
          @update:open="(o) => (showOptions = o)"
          @update:modelValue="onSelect"
          :ignore-filter="true"
          highlight-on-hover
        >
          <ComboboxAnchor
            class="flex h-7 max-w-full w-auto items-center gap-2 rounded px-2 py-1 border border-transparent"
            :class="[
              variant == 'ghost'
                ? 'bg-surface-white hover:bg-surface-white'
                : 'bg-surface-gray-2 hover:bg-surface-gray-3',
              inputClass,
            ]"
          >
            <ComboboxInput
              ref="search"
              :value="query"
              autocomplete="off"
              class="bg-transparent p-0 outline-none border-0 text-base text-ink-gray-8 h-full placeholder:text-ink-gray-4 w-full focus:outline-none focus:ring-0 focus:border-0"
              :placeholder="placeholder"
              @focus="showOptions = true"
              @input="onInput"
              @keydown.delete.capture.stop="removeLastValue"
              @keydown.enter.prevent="handleEnter"
            />
          </ComboboxAnchor>
          <ComboboxPortal>
            <ComboboxContent
              class="z-10 mt-1 min-w-48 w-auto max-w-96 bg-surface-modal overflow-hidden rounded-lg shadow-2xl ring-1 ring-black ring-opacity-5"
              position="popper"
              :align="'start'"
              @openAutoFocus.prevent
              @closeAutoFocus.prevent
            >
              <ComboboxViewport class="max-h-60 overflow-auto p-1.5">
                <ComboboxEmpty
                  class="flex gap-2 rounded px-2 py-1 text-base text-ink-gray-5"
                >
                  <FeatherIcon name="search" class="h-4" />
                  {{ __(emptyPlaceholder) }}
                </ComboboxEmpty>
                <ComboboxItem
                  v-for="option in options"
                  :key="option.value"
                  :value="option.value"
                  class="text-base leading-none text-ink-gray-7 rounded flex items-center px-2 py-1 relative select-none data-[highlighted]:outline-none data-[highlighted]:bg-surface-gray-3 cursor-pointer"
                  @mousedown.prevent="onSelect(option.value)"
                >
                  <UserAvatar class="mr-2" :name="option.value" size="lg" />
                  <div class="flex flex-col gap-1 p-1 text-ink-gray-8">
                    <div class="text-base font-medium">{{ option.label }}</div>
                    <div class="text-sm text-ink-gray-5">
                      {{ option.value }}
                    </div>
                  </div>
                </ComboboxItem>
              </ComboboxViewport>
            </ComboboxContent>
          </ComboboxPortal>
        </ComboboxRoot>
      </div>
    </div>
    <ErrorMessage class="mt-2 pl-2" v-if="error" :message="error" />
    <div
      v-if="info"
      class="whitespace-pre-line text-sm text-ink-blue-3 mt-2 pl-2"
    >
      {{ info }}
    </div>
  </div>
</template>

<script setup>
import UserAvatar from "@/components/UserAvatar.vue";
import { useUserStore } from "@/stores/user";
import { watchDebounced } from "@vueuse/core";
import { createResource } from "frappe-ui";
import {
  ComboboxAnchor,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxPortal,
  ComboboxRoot,
  ComboboxViewport,
} from "reka-ui";
import { computed, nextTick, ref, watch } from "vue";

const props = defineProps({
  forAgents: { type: Boolean, default: true },
  validate: { type: Function, default: null },
  emptyPlaceholder: { type: String, default: __("No results found") },
  variant: { type: String, default: "subtle" },
  placeholder: { type: String, default: "" },
  inputClass: { type: String, default: "" },
  existingUsers: { type: Array, default: () => [] },
});

const errorMessage = (value) => __("{0} is an Invalid Email Address", [value]);

// v-model values
const values = defineModel();

// Common state
const emails = ref([]);
const search = ref(null);
const error = ref(null);
const info = ref(null);
const query = ref("");
const showOptions = ref(false);
const tempSelection = ref(null);

const { users } = useUserStore();

// --- Contacts resource (used when forAgents = false) ---
const filterContacts = createResource({
  url: "helpdesk.api.contact.search_contacts",
  method: "GET",
  params: { txt: "" },
  transform: (data) =>
    data.map(({ full_name, email_id, name }) => ({
      label: email_id || full_name || name,
      value: name,
      email: email_id,
    })),
});

watchDebounced(
  query,
  (val) => {
    if (props.forAgents) return;
    console.log("Updating contacts filter with", props.existingUsers);
    filterContacts.update({ params: { txt: val || "" } });
    filterContacts.reload();
  },
  { debounce: 250, immediate: true }
);

// --- Options ---
const options = computed(() => {
  if (props.forAgents) {
    let list = (users?.data || []).map((u) => ({
      label: u.full_name || u.name,
      value: u.name,
    }));
    if (values.value?.length) {
      list = list.filter((o) => !values.value.includes(o.value));
    }
    if (props.existingUsers?.length) {
      list = list.filter((o) => !props.existingUsers.includes(o.value));
    }
    if (query.value) {
      const q = query.value.toLowerCase();
      list = list.filter(
        (o) =>
          o.label?.toLowerCase().includes(q) ||
          o.value?.toLowerCase().includes(q)
      );
    }
    return list;
  }

  // contacts mode
  let list = filterContacts.data || [];
  if (values.value?.length) {
    list = list.filter((o) => !values.value.includes(o.value));
  }
  if (props.existingUsers?.length) {
    list = list.filter((o) => !props.existingUsers.includes(o.email));
  }
  return list;
});

function addValue(input) {
  if (!input) return;
  error.value = null;
  info.value = null;
  const parts = input
    .split(",")
    .map((p) => p.trim())
    .filter(Boolean);
  for (const email of parts) {
    const inList = options.value.some((o) => o.value === email);
    if (!inList) {
      error.value = props.forAgents
        ? __("{0} is not an existing user", [email])
        : __("{0} is not an existing contact", [email]);
      query.value = email;
      break;
    }
    if (props.validate && props.forAgents && !props.validate(email)) {
      error.value = errorMessage(email);
      query.value = email;
      break;
    }
    if (!values.value) values.value = [email];
    else values.value.push(email);
  }
}

function removeValue(value) {
  values.value = values.value.filter((v) => v !== value);
}

function removeLastValue() {
  if (query.value) return;
  let emailRef = emails.value[emails.value.length - 1]?.rootRef;
  if (document.activeElement === emailRef) {
    values.value.pop();
    nextTick(() => {
      if (values.value.length) {
        emailRef = emails.value[emails.value.length - 1].rootRef;
        emailRef?.focus();
      } else {
        setFocus();
      }
    });
  } else {
    emailRef?.focus();
  }
}

function setFocus() {
  setTimeout(() => {
    search.value?.$el?.focus();
  }, 200);
}

function onInput(e) {
  query.value = e.target.value;
  showOptions.value = true;
}

function onSelect(val) {
  if (!val) return;
  addValue(val);
  if (!error.value) {
    query.value = "";
    tempSelection.value = null;
    showOptions.value = true;
    nextTick(() => setFocus());
  }
}

function handleEnter() {
  if (query.value) onSelect(query.value);
}

watch(options, (list) => {
  tempSelection.value = list[0]?.value ?? null;
});

defineExpose({ setFocus });
</script>
