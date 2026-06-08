<template>
  <div class="flex flex-col gap-3">
    <!-- Action rows -->
    <div
      v-for="(action, index) in actions"
      :key="index"
      class="flex items-start gap-2"
    >
      <!-- Step label -->
      <div class="w-8 shrink-0 text-right pt-1.5">
        <span class="text-xs font-medium text-green-600">{{ index + 1 }}.</span>
      </div>

      <!-- Action type select -->
      <div class="w-52 shrink-0">
        <FormControl
          type="select"
          :options="actionTypeOptions"
          :modelValue="action.type"
          @update:modelValue="(val) => updateAction(index, 'type', val)"
          class="w-full"
        />
      </div>

      <!-- Value input (dynamic per action type) -->
      <div class="flex-1 min-w-0">
        <!-- Text input for most actions -->
        <FormControl
          v-if="getValueType(action.type) === 'text'"
          type="text"
          :placeholder="getValuePlaceholder(action.type)"
          :modelValue="action.value"
          @update:modelValue="(val) => updateAction(index, 'value', val)"
          class="w-full"
        />

        <!-- Textarea for add_internal_note -->
        <FormControl
          v-else-if="getValueType(action.type) === 'textarea'"
          type="textarea"
          :placeholder="__('Note content...')"
          :modelValue="action.value"
          @update:modelValue="(val) => updateAction(index, 'value', val)"
          class="w-full"
          :rows="2"
        />

        <!-- Priority select -->
        <FormControl
          v-else-if="getValueType(action.type) === 'priority'"
          type="select"
          :options="PRIORITY_OPTIONS"
          :modelValue="action.value"
          @update:modelValue="(val) => updateAction(index, 'value', val)"
          class="w-full"
        />

        <!-- Status select -->
        <FormControl
          v-else-if="getValueType(action.type) === 'status'"
          type="select"
          :options="STATUS_OPTIONS"
          :modelValue="action.value"
          @update:modelValue="(val) => updateAction(index, 'value', val)"
          class="w-full"
        />

        <!-- URL input for webhook -->
        <FormControl
          v-else-if="getValueType(action.type) === 'url'"
          type="url"
          :placeholder="__('https://example.com/webhook')"
          :modelValue="action.value"
          @update:modelValue="(val) => updateAction(index, 'value', val)"
          class="w-full"
        />

        <!-- No value needed -->
        <div v-else class="h-7 rounded border border-gray-200 bg-gray-50 flex items-center px-2">
          <span class="text-xs text-gray-400 italic">{{ __("— select action type —") }}</span>
        </div>
      </div>

      <!-- Move up / down -->
      <div class="flex flex-col gap-0.5 shrink-0">
        <button
          class="rounded p-0.5 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
          :disabled="index === 0"
          :title="__('Move up')"
          @click="moveAction(index, -1)"
        >
          <LucideChevronUp class="h-3 w-3" />
        </button>
        <button
          class="rounded p-0.5 text-gray-400 hover:bg-gray-100 disabled:opacity-30"
          :disabled="index === actions.length - 1"
          :title="__('Move down')"
          @click="moveAction(index, 1)"
        >
          <LucideChevronDown class="h-3 w-3" />
        </button>
      </div>

      <!-- Remove button -->
      <button
        class="shrink-0 rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500 transition-colors mt-0.5"
        :title="__('Remove action')"
        @click="removeAction(index)"
      >
        <LucideX class="h-3.5 w-3.5" />
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="actions.length === 0"
      class="rounded-md border border-dashed border-gray-200 px-4 py-3 text-center"
    >
      <p class="text-sm text-gray-400">
        {{ __("Add at least one action to execute when this rule fires.") }}
      </p>
    </div>

    <!-- Add action button -->
    <div>
      <Button
        variant="ghost"
        size="sm"
        :label="__('Add Action')"
        @click="addAction"
      >
        <template #prefix>
          <LucidePlus class="h-3.5 w-3.5" />
        </template>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue"
import { Button, FormControl } from "frappe-ui"
import { __ } from "@/translation"
import LucideX from "~icons/lucide/x"
import LucidePlus from "~icons/lucide/plus"
import LucideChevronUp from "~icons/lucide/chevron-up"
import LucideChevronDown from "~icons/lucide/chevron-down"
import { ACTION_OPTIONS, PRIORITY_OPTIONS, STATUS_OPTIONS } from "./actionOptions"

interface Action {
  type: string
  value: string
}

const props = defineProps<{
  modelValue: Action[]
}>()

const emit = defineEmits<{
  (e: "update:modelValue", value: Action[]): void
}>()

const actions = ref<Action[]>(props.modelValue || [])

// Guard flag prevents the two-way watcher loop: local→emit→prop→local→...
let _syncingFromProp = false

watch(actions, (val) => {
  if (_syncingFromProp) return
  emit("update:modelValue", val)
}, { deep: true })

watch(() => props.modelValue, (val) => {
  _syncingFromProp = true
  actions.value = val || []
  _syncingFromProp = false
}, { deep: true })

const actionTypeOptions = computed(() => [
  { label: "— Select action —", value: "" },
  ...ACTION_OPTIONS.map((a) => ({ label: a.label, value: a.value })),
])

function getValueType(actionType: string): string {
  const found = ACTION_OPTIONS.find((a) => a.value === actionType)
  return found?.valueType || "none"
}

function getValuePlaceholder(actionType: string): string {
  const placeholders: Record<string, string> = {
    assign_to_agent: "agent@example.com",
    assign_to_team: "Team name",
    set_category: "Category name",
    add_tag: "tag-name",
    send_email: "recipient@example.com",
    send_notification: "Notification message...",
  }
  return placeholders[actionType] || "Value"
}

function addAction() {
  actions.value = [...actions.value, { type: "", value: "" }]
}

function removeAction(index: number) {
  actions.value = actions.value.filter((_, i) => i !== index)
}

function updateAction(index: number, key: keyof Action, value: string) {
  const updated = [...actions.value]
  updated[index] = { ...updated[index], [key]: value }
  // Reset value when type changes
  if (key === "type") {
    updated[index].value = ""
  }
  actions.value = updated
}

function moveAction(index: number, direction: -1 | 1) {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= actions.value.length) return
  const updated = [...actions.value]
  const temp = updated[index]
  updated[index] = updated[newIndex]
  updated[newIndex] = temp
  actions.value = updated
}
</script>
