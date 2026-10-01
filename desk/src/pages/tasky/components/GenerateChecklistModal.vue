<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/25 backdrop-blur-sm"
    @click.self="$emit('close')"
  >
    <div class="bg-surface-white border border-outline-gray-2 rounded-xl shadow-xl w-full max-w-md overflow-hidden">
      <div class="flex items-center justify-between px-5 py-4 border-b border-outline-gray-2">
        <h2 class="text-base-semibold text-ink-gray-9">Generate Checklist</h2>
        <button @click="$emit('close')" class="size-7 flex items-center justify-center rounded hover:bg-surface-gray-1 text-ink-gray-5 transition-colors">
          <LucideX class="size-4" />
        </button>
      </div>

      <div class="px-5 py-5">
        <div v-if="templates.loading" class="text-sm text-ink-gray-5 py-4">Loading templates...</div>
        <div v-else-if="templates.error" class="text-sm text-ink-gray-5 py-4">Failed to load templates</div>
        <div v-else>
          <label class="block text-xs font-medium text-ink-gray-6 mb-1.5">Template</label>
          <select
            v-model="selectedTemplate"
            class="w-full border border-outline-gray-2 rounded-lg px-3 py-2 text-sm text-ink-gray-9 bg-surface-white focus:outline-none focus:border-outline-gray-4"
          >
            <option value="" disabled>Select a template...</option>
            <option v-for="t in templates.data" :key="t.name" :value="t.name">
              {{ t.template_name }}{{ t.industry ? ' · ' + t.industry : '' }}
            </option>
          </select>

          <div v-if="selectedTemplate" class="mt-3 rounded-lg bg-surface-gray-1 border border-outline-gray-2 p-3 text-sm text-ink-gray-6">
            <template v-if="templates.data">
              <span v-for="t in templates.data" :key="t.name">
                <template v-if="t.name === selectedTemplate">{{ t.description || t.industry + ' implementation template' }}</template>
              </span>
            </template>
          </div>

          <div v-if="generateTask.loading" class="text-sm text-ink-gray-5 mt-3 py-2">Generating tasks...</div>
          <div v-else-if="generateTask.error" class="text-sm text-ink-gray-5 mt-3 py-2">{{ generateTask.error }}</div>
          <div v-else-if="generateTask.data" class="text-sm text-ink-gray-9 mt-3 py-2 font-medium">{{ generateTask.data.tasks_created }} tasks created</div>
        </div>
      </div>

      <div class="flex justify-end gap-2 px-5 py-3 border-t border-outline-gray-2 bg-surface-gray-1">
        <button
          @click="$emit('close')"
          class="px-4 py-2 text-sm text-ink-gray-7 hover:text-ink-gray-9 hover:bg-surface-gray-2 rounded-lg transition-colors"
        >
          Cancel
        </button>
        <button
          @click="generate"
          :disabled="!selectedTemplate || generateTask.loading"
          class="px-5 py-2 text-sm font-medium rounded-lg bg-ink-gray-9 text-ink-white hover:bg-ink-gray-8 disabled:opacity-40 transition-colors"
        >
          {{ generateTask.loading ? "Generating..." : "Generate" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { createResource } from "frappe-ui";
import LucideX from "~icons/lucide/x";

const props = defineProps<{
  show: boolean;
  projectId: string;
}>();

const emit = defineEmits<{
  close: [];
  generated: [];
}>();

const selectedTemplate = ref("");

const templates = createResource({
  url: "helpdesk.tasky.api.get_templates",
  auto: true,
  transform: (d: any) => d ?? [],
});

const generateTask = createResource({
  url: "helpdesk.tasky.api.generate_checklist",
  onSuccess() {
    setTimeout(() => emit("generated"), 800);
  },
});

function generate() {
  if (!selectedTemplate.value) return;
  generateTask.submit({
    project: props.projectId,
    template: selectedTemplate.value,
  });
}
</script>
