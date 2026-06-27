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
        :tooltip="copyOnClick ? __('Click to copy') : undefined"
        :class="[
          {
            'rounded border !bg-surface-base  hover:!bg-surface-gray-1 focus-visible:ring-outline-gray-4':
              variant === 'subtle',
          },
          copyOnClick
            ? 'cursor-pointer transition-transform active:scale-[0.98]'
            : '',
        ]"
        @click="copyOnClick ? copy(value) : null"
        @keydown.delete.capture.stop="removeLastValue"
      >
        <template #suffix>
          <span
            class="lucide-x h-3.5"
            aria-hidden="true"
            @click.stop="removeValue(value)"
          />
        </template>
      </Button>
      <div class="flex-1 min-w-32">
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
                ? 'bg-surface-base hover:bg-surface-base'
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
              @keydown="onKeydown"
              @paste="onPaste"
            />
          </ComboboxAnchor>
          <ComboboxPortal>
            <ComboboxContent
              class="z-10 mt-1 min-w-48 w-auto max-w-96 bg-surface-elevation-2 overflow-hidden rounded-lg shadow-2xl ring-1 ring-black ring-opacity-5"
              position="popper"
              :align="'start'"
              @openAutoFocus.prevent
              @closeAutoFocus.prevent
            >
              <ComboboxViewport class="max-h-60 overflow-auto p-1.5">
                <ComboboxEmpty
                  class="flex gap-2 rounded px-2 py-1 text-base text-ink-gray-5"
                >
                  <span class="lucide-search h-4" aria-hidden="true" />
                  {{ __(emptyPlaceholder) }}
                </ComboboxEmpty>
                <ComboboxItem
                  v-for="option in options"
                  :key="option.value"
                  :value="option.value"
                  class="text-base leading-none text-ink-gray-7 rounded flex items-center px-2 py-1 relative select-none data-[highlighted]:outline-none data-[highlighted]:bg-surface-gray-3 cursor-pointer"
                  @mousedown.prevent="onSelect(option.value)"
                >
                  <UserAvatar
                    class="mr-0.5"
                    :name="getUsernameLabel(option.label)"
                    size="lg"
                  />
                  <div class="flex flex-col gap-1 p-1 text-ink-gray-8">
                    <div class="text-base-medium">
                      {{ getUsernameLabel(option.label) }}
                    </div>
                    <div class="text-sm text-ink-gray-5">
                      {{ option.isCustom ? customEmailLabel : option.value }}
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
      class="whitespace-pre-line text-sm text-ink-blue-6 mt-2 pl-2"
    >
      {{ info }}
    </div>
  </div>
</template>

<script setup>
import UserAvatar from "@/components/UserAvatar.vue";
import { useUserStore } from "@/stores/user";
import { copy } from "@/utils";
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
import { computed, nextTick, onMounted, ref, watch } from "vue";

const props = defineProps({
  // "contact" searches HD contacts; "agents" picks from the user store.
  scope: { type: String, default: "contact" },
  validate: { type: Function, default: null },
  emptyPlaceholder: { type: String, default: __("No results found") },
  variant: { type: String, default: "subtle" },
  placeholder: { type: String, default: "" },
  inputClass: { type: String, default: "" },
  existingUsers: { type: Array, default: () => [] },
  allowCustomEmail: { type: Boolean, default: false },
  additionalFilters: { type: Array, default: () => [] },
  copyOnClick: { type: Boolean, default: false },
  customEmailLabel: { type: String, default: __("Invite via email") },
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

// --- Contacts resource (used when scope = "contact") ---
const filterContacts = createResource({
  url: "helpdesk.api.contact.search_contacts",
  method: "GET",
  params: contactSearchParams(""),
  transform: (data) =>
    data.map(({ full_name, email_id, name }) => ({
      label: full_name || email_id || name,
      value: email_id || name,
      email: email_id,
    })),
});

watchDebounced(
  query,
  (newVal) => {
    if (props.scope === "agents") return;
    filterContacts.update({ params: contactSearchParams(newVal) });
    filterContacts.reload();
  },
  { debounce: 250, immediate: true }
);

function contactSearchParams(txt) {
  const params = { txt: txt || "" };
  if (props.additionalFilters?.length) {
    params.additional_filters = JSON.stringify(props.additionalFilters);
  }
  return params;
}

// --- Options ---
const options = computed(() => {
  if (props.scope === "agents") {
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
    list = list.filter((o) => !isExistingUser(o.email));
  }
  // offer the typed text itself when nothing matches, like the email To field
  if (
    props.allowCustomEmail &&
    query.value &&
    !list.length &&
    !isExistingUser(query.value)
  ) {
    list = [{ label: query.value, value: query.value, isCustom: true }];
  }
  return list;
});

function isExistingUser(email) {
  if (!email) return false;
  return props.existingUsers?.some(
    (user) => user?.toLowerCase?.() === email.toLowerCase()
  );
}

function addValue(input) {
  if (!input) return;
  error.value = null;
  info.value = null;
  const parts = splitRecipients(input);
  for (const email of parts) {
    if (values.value?.includes(email)) continue;
    const inList = options.value.some((o) => o.value === email && !o.isCustom);
    if (!inList && !canAddCustomValue(email)) break;
    if (!values.value) values.value = [email];
    else values.value.push(email);
  }
}

function canAddCustomValue(email) {
  if (!props.allowCustomEmail) {
    error.value =
      props.scope === "agents"
        ? __("{0} is not an existing user", [email])
        : __("{0} is not an existing contact", [email]);
    query.value = email;
    return false;
  }
  if (isExistingUser(email)) {
    error.value = __("{0} is already added", [email]);
    query.value = email;
    return false;
  }
  if (props.validate && !props.validate(email)) {
    error.value = errorMessage(email);
    query.value = email;
    return false;
  }
  return true;
}

// Split on commas/semicolons/newlines while keeping a quoted display name
// intact, so '"Doe, John" <a@b.com>' stays a single token.
function splitRecipients(input) {
  const parts = [];
  let current = "";
  let inQuotes = false;
  for (const char of input) {
    if (char === '"') {
      inQuotes = !inQuotes;
      current += char;
    } else if ((char === "," || char === ";" || char === "\n") && !inQuotes) {
      if (current.trim()) parts.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  if (current.trim()) parts.push(current.trim());
  return parts;
}

// Reduce a "Name <email>" value to just the display name for rendering.
function getUsernameLabel(value) {
  if (!value) return "";
  return value.split("<")[0].replace(/"/g, "").trim();
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
  error.value = null;
  info.value = null;
  showOptions.value = true;
}

function onSelect(val) {
  if (!val) return;
  addValue(val);
  if (error.value) {
    showOptions.value = false;
    return;
  }
  query.value = "";
  tempSelection.value = null;
  showOptions.value = true;
  nextTick(() => setFocus());
}

// Commit the current query as a pill on Enter, comma or space.
function onKeydown(e) {
  const isCommitKey = e.key === "Enter" || e.key === "," || e.key === " ";
  if (!isCommitKey || !query.value.trim()) return;
  e.preventDefault();
  onSelect(query.value);
}

// Split a pasted, comma/space/newline-separated list into multiple pills.
function onPaste(e) {
  const text = e.clipboardData?.getData("text") ?? "";
  if (!/[\s,;]/.test(text)) return;
  e.preventDefault();
  addValue(text);
  if (!error.value) {
    query.value = "";
    tempSelection.value = null;
    nextTick(() => setFocus());
  }
}

watch(options, (list) => {
  tempSelection.value = list[0]?.value ?? null;
});

onMounted(() => {
  // reka-ui hardcodes autocomplete="off", which Chrome ignores for fields it
  // reads as email/address. "new-password" is the value Chrome won't autofill,
  // so its native address dropdown stops covering our options. (No password UI:
  // the input is type=text and not inside a form.)
  search.value?.$el?.setAttribute("autocomplete", "new-password");
});

defineExpose({ setFocus });
</script>
