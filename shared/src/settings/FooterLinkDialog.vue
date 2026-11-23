<template>
  <Dialog v-model:open="open" size="sm" :title="title">
    <form class="flex flex-col gap-4" @submit.prevent="save">
      <TextInput
        v-if="isNewColumn"
        v-model="newColumnTitle"
        :label="__('Column title')"
        :placeholder="__('Company')"
      />
      <TextInput
        v-model="form.label"
        :label="__('Label')"
        :placeholder="__('Contact sales')"
      />
      <TextInput
        v-model="form.url"
        :error="linkError(form.url)"
        :label="__('URL')"
        :placeholder="__('https://example.com/contact')"
      />
      <Switch v-model="form.open_in_new_tab" :label="__('Open in new tab')" />
      <Button
        class="mt-2 self-end"
        type="submit"
        variant="solid"
        :label="submitLabel"
        :disabled="!canSave"
      />
    </form>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, Dialog, Switch, TextInput } from "frappe-ui";
import { computed, reactive, ref, watch } from "vue";
import type { KnowledgeBaseLink } from "../knowledgeBasePreview";
import { __ } from "../translation";
import { isValidLink, linkError } from "../utils";

const props = defineProps<{
  link?: KnowledgeBaseLink;
  columnTitle?: string;
  isNewColumn?: boolean;
}>();
const emit = defineEmits<{
  save: [link: KnowledgeBaseLink, columnTitle: string];
}>();
const open = defineModel<boolean>("open", { required: true });

const form = reactive<KnowledgeBaseLink>(newLink());
const newColumnTitle = ref("");

const title = computed(() => {
  if (props.link) return __("Edit link");
  if (props.isNewColumn) return __("Add column");
  return __("Add link to {0}", [props.columnTitle || __("Untitled")]);
});
const submitLabel = computed(() => {
  if (props.link) return __("Done");
  return props.isNewColumn ? __("Add column") : __("Add link");
});
const canSave = computed(
  () => (!props.isNewColumn || newColumnTitle.value.trim()) && isValidLink(form)
);

watch(open, (isOpen) => {
  if (!isOpen) return;
  Object.assign(form, props.link || newLink());
  newColumnTitle.value = "";
});

function newLink(): KnowledgeBaseLink {
  return { label: "", url: "", open_in_new_tab: true };
}

function save() {
  if (!canSave.value) return;
  emit(
    "save",
    { ...form, label: form.label.trim(), url: form.url.trim() },
    newColumnTitle.value.trim()
  );
  open.value = false;
}
</script>
