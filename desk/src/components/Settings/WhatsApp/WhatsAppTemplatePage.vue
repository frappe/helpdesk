<template>
  <SettingsLayoutBase
    :back-label="title"
    :on-back="() => leave(() => emit('back'))"
    :dirty="isDirty && !template.isNew"
  >
    <template v-if="loaded" #header-actions>
      <div class="flex gap-2">
        <Button
          :label="preview ? __('Edit') : __('Preview')"
          :icon-left="preview ? 'lucide-pencil' : 'lucide-eye'"
          @click="preview = !preview"
        />
        <Button
          v-if="template.editable && (isDirty || template.isNew)"
          :label="template.isNew ? __('Create') : __('Save')"
          :loading="template.saving"
          theme="gray"
          variant="solid"
          @click="save"
        />
      </div>
    </template>
    <template #content>
      <div
        v-if="template.loading"
        class="flex items-center justify-center py-16 text-ink-gray-5"
      >
        <LoadingIndicator class="size-4" />
      </div>
      <Alert
        v-else-if="!loaded"
        theme="red"
        :title="__('Could not load this template')"
        :primary-action="{ label: __('Retry'), onClick: template.reload }"
      />
      <TemplatePreview v-else-if="preview" :controller="template" />
      <TemplateForm v-else :controller="template" />
    </template>
  </SettingsLayoutBase>
  <ConfirmDialog
    v-model="confirming"
    :title="__('Unsaved changes')"
    :message="
      __('Are you sure you want to go back? Unsaved changes will be lost.')
    "
    :on-confirm="confirm"
  />
</template>

<script setup lang="ts">
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import {
  serverErrorMessage,
  TemplateForm,
  TemplatePreview,
  useTemplate,
} from "@whatsapp/ui";
import { Alert, Button, LoadingIndicator, toast } from "frappe-ui";
import { computed, ref } from "vue";
import { useUnsavedGuard } from "./useUnsavedGuard";

const props = defineProps<{ name: string; defaultAccount?: string }>();
const emit = defineEmits<{ back: [] }>();

const template = useTemplate({ name: () => props.name });
const preview = ref(false);
// An existing template counts as loaded once the server copy is in the form
const loaded = computed(() => template.isNew || Boolean(template.doc.name));

// Its variables pick from ticket fields, and Meta needs an account to review it
if (template.isNew) {
  template.doc.reference_doctype = "HD Ticket";
  template.doc.whatsapp_account = props.defaultAccount;
}
// The default above is not an edit, so a new form left untouched leaves without asking
const untouched = JSON.stringify(template.doc);

const isDirty = computed(() => {
  if (template.isNew) return JSON.stringify(template.doc) !== untouched;
  return loaded.value && template.isDirty;
});
const { confirming, leave, confirm } = useUnsavedGuard(() => isDirty.value);

const title = computed(() => {
  if (template.isNew) return __("New template");
  return template.doc.template_label || template.doc.template_name || "";
});

/** Saving sends the template to Meta; the toast repeats a refusal the long form shows far below. */
async function save() {
  const wasNew = template.isNew;
  if (!(await template.save())) {
    toast.error(
      serverErrorMessage(template.error) || __("Could not save the template")
    );
    return;
  }
  if (!wasNew) return toast.success(__("Template updated"));
  toast.success(__("Template created and sent to Meta for review"));
  emit("back");
}
</script>
