<template>
  <Dialog v-model:open="show" :title="__('WhatsApp Templates')" size="4xl">
    <template #default>
      <TextInput
        v-model="search"
        type="text"
        :placeholder="__('Search templates')"
        :aria-label="__('Search templates')"
      >
        <template #prefix>
          <span
            class="lucide-search size-4 text-ink-gray-4"
            aria-hidden="true"
          />
        </template>
      </TextInput>
      <div
        v-if="templates.loading && !templates.templates.length"
        class="grid h-56 place-items-center"
      >
        <LoadingIndicator class="size-5 text-ink-gray-4" />
      </div>
      <div
        v-else-if="!filtered.length"
        class="flex h-56 flex-col items-center justify-center gap-1 text-center"
      >
        <p class="text-base text-ink-gray-7">
          {{
            search ? __("No matching templates") : __("No approved templates")
          }}
        </p>
        <p class="text-p-sm text-ink-gray-5">
          {{ __("Templates approved by Meta for this number show up here.") }}
        </p>
      </div>
      <div
        v-else
        class="mt-3 grid max-h-[60vh] grid-cols-1 gap-3 overflow-y-auto p-0.5 sm:grid-cols-3"
      >
        <button
          v-for="template in filtered"
          :key="template.name"
          type="button"
          class="flex h-56 flex-col gap-2.5 rounded-6 border border-outline-gray-2 bg-surface-gray-1 p-3 text-start transition-colors hover:bg-surface-gray-2"
          :class="{ 'ring-2 ring-outline-gray-4': selected === template.name }"
          :aria-pressed="selected === template.name"
          @click="selected = template.name"
        >
          <span
            class="flex w-full items-center gap-2 border-b border-outline-gray-2 pb-2"
          >
            <span class="truncate text-base font-medium text-ink-gray-9">
              {{ template.template_label || template.template_name }}
            </span>
            <Badge v-if="template.language" theme="gray" variant="subtle">
              {{ template.language }}
            </Badge>
          </span>
          <TemplateContent
            class="min-h-0 w-full flex-1 text-p-sm text-ink-gray-9"
            :header="fill(template, template.header_text)"
            :body="fill(template, template.message)"
            :footer="template.footer"
            :buttons="template.buttons"
            body-class="min-h-0 flex-1 overflow-y-auto"
          />
        </button>
      </div>
      <div class="mt-4 flex items-center justify-between gap-4">
        <ErrorMessage :message="sendError" />
        <Button
          class="ms-auto"
          variant="solid"
          :label="__('Send')"
          :disabled="!selected || !to"
          :loading="sending"
          @click="send"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import {
  TemplateContent,
  useTemplates,
  type WhatsAppTemplate,
} from "@whatsapp/ui";
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  LoadingIndicator,
  TextInput,
} from "frappe-ui";
import { computed, ref, watch } from "vue";

const props = defineProps<{
  ticket: Record<string, any>;
  to?: string | null;
  /** names of the templates the ticket's Business Number may send */
  allowed: string[];
}>();
const emit = defineEmits<{ sent: [] }>();
const show = defineModel<boolean>({ default: false });

const search = ref("");
const selected = ref("");
const sending = ref(false);
const sendError = ref("");

const templates = useTemplates({
  referenceDoctype: "HD Ticket",
  referenceDocname: () => props.ticket.name,
  to: () => props.to ?? undefined,
});

const filtered = computed(() => {
  const query = search.value.toLowerCase();
  return templates.templates.filter(
    (template) =>
      props.allowed.includes(template.name) &&
      [template.template_label, template.template_name, template.language].some(
        (text) => text?.toLowerCase().includes(query)
      )
  );
});

// mirrors the server: a mapped `{{name}}` takes the ticket's value, an unmapped one stays visible
function fill(template: WhatsAppTemplate, text?: string): string | undefined {
  const fields = Object.fromEntries(
    (template.template_variables ?? [])
      .filter((variable) => variable.variable_field)
      .map((variable) => [variable.variable_name, variable.variable_field])
  );
  return text?.replace(/\{\{\s*(\w+)\s*\}\}/g, (match, name) =>
    name in fields ? String(props.ticket[fields[name]] ?? "") : match
  );
}

async function send() {
  sending.value = true;
  sendError.value = "";
  const sent = await templates.sendTemplate(selected.value);
  sending.value = false;
  if (!sent) {
    sendError.value = errorText(templates.error);
    return;
  }
  show.value = false;
  emit("sent");
}

function errorText(error: any): string {
  return (
    error?.messages?.[0] || error?.message || __("Could not send the template")
  );
}

watch(selected, () => (sendError.value = ""));

watch(show, (open) => {
  if (!open) return;
  selected.value = "";
  search.value = "";
  templates.reload();
});
</script>
