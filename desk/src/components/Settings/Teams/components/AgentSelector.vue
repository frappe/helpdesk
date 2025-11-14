<template>
  <div
    class="flex flex-wrap gap-1 bg-surface-gray-2 p-0.5 border rounded w-full"
  >
    <Button
      ref="emails"
      v-for="value in values"
      :key="value"
      :label="value"
      theme="gray"
      variant="outline"
      @keydown.delete.capture.stop="removeLastValue"
      class="active:bg-surface-gray-1 active:border-outline-gray-2 hover:border-outline-gray-2 hover:bg-surface-gray-1"
    >
      <template #prefix>
        <UserAvatar :name="value" size="xs" />
      </template>
      <template #suffix>
        <FeatherIcon class="h-3.5" name="x" @click.stop="removeValue(value)" />
      </template>
    </Button>
    <div class="flex-1">
      <ComboboxRoot
        :model-value="tempSelection"
        :open="showOptions"
        @update:open="(o) => (showOptions = o)"
        :ignore-filter="true"
        @update:modelValue="onSelect"
      >
        <ComboboxAnchor
          class="flex h-7 w-full items-center gap-2 rounded px-2 py-1 border border-transparent bg-surface-gray-2 hover:bg-surface-gray-2"
        >
          <ComboboxInput
            ref="search"
            :value="query"
            autocomplete="off"
            class="bg-transparent p-0 outline-none border-0 text-base text-ink-gray-8 h-full placeholder:text-ink-gray-4 focus:outline-none focus:ring-0 focus:border-0 w-full select-none"
            placeholder="Type agent name or email"
            @focus="showOptions = true"
            @click="showOptions = true"
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
                Agent not found
              </ComboboxEmpty>
              <ComboboxItem
                v-for="agent in agentsList"
                :key="agent.name"
                :value="agent.name"
                class="text-base leading-none text-ink-gray-7 rounded flex items-center px-2 py-1 relative select-none data-[highlighted]:outline-none data-[highlighted]:bg-surface-gray-3 cursor-pointer"
              >
                <UserAvatar class="mr-1" :name="agent.agent_name" size="lg" />
                <div class="flex flex-col gap-1 p-1 text-ink-gray-8">
                  <div class="text-base font-medium">
                    {{ agent.agent_name }}
                  </div>
                  <div class="text-sm text-ink-gray-5">
                    {{ agent.name }}
                  </div>
                </div>
              </ComboboxItem>
            </ComboboxViewport>
          </ComboboxContent>
        </ComboboxPortal>
      </ComboboxRoot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { UserAvatar } from "@/components";
import { useAgentStore } from "@/stores/agent";
import { Button } from "frappe-ui";
import { storeToRefs } from "pinia";
import {
  ComboboxRoot,
  ComboboxAnchor,
  ComboboxInput,
  ComboboxPortal,
  ComboboxContent,
  ComboboxViewport,
  ComboboxItem,
  ComboboxEmpty,
} from "reka-ui";
import { computed, nextTick, ref } from "vue";

const values = defineModel<any[]>();

const emit = defineEmits(["change"]);

const props = defineProps({
  existingAgents: {
    type: Array,
    default: () => [],
  },
});

const emails = ref([]);
const search = ref(null);
const query = ref("");
const showOptions = ref(false);
const tempSelection = ref(null);

const { agents } = storeToRefs(useAgentStore());

const agentsList = computed(() => {
  let list = agents.value.data;
  if (query.value) {
    list = list.filter(
      (agent) =>
        agent.agent_name.toLowerCase().includes(query.value.toLowerCase()) ||
        agent.name.toLowerCase().includes(query.value.toLowerCase())
    );
  }

  if (props.existingAgents.length) {
    list = list.filter((agent) => !props.existingAgents.includes(agent.name));
  }
  if (values.value.length) {
    list = list.filter((agent) => !values.value.includes(agent.name));
  }
  return list;
});

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

function onSelect(val) {
  if (!val) return;

  if (!values.value) values.value.push(val);
  else values.value.push(val);
  query.value = "";
  emit("change", values.value);
}

function onInput(e) {
  query.value = e.target.value;
  showOptions.value = true;
}

function handleEnter() {
  if (query.value) onSelect(query.value);
}

function setFocus() {
  search.value?.focus?.();
}
</script>
