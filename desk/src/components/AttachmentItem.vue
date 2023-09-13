<template>
  <span>
    <a :href="isShowable ? null : url" target="_blank">
      <Button
        :label="label"
        theme="gray"
        variant="outline"
        @click="toggleDialog()"
      >
        <template #prefix>
          <component :is="getIcon()" class="h-4 w-4" />
        </template>
        <template #suffix>
          <slot name="suffix" />
        </template>
      </Button>
    </a>
    <Dialog
      v-model="showDialog"
      :options="{
        title: label,
        size: '4xl',
      }"
    >
      <template #body-content>
        <div
          v-if="isText"
          class="prose prose-sm max-w-none whitespace-pre-wrap"
        >
          {{ content }}
        </div>
        <img v-if="isImage" :src="url" class="m-auto rounded border" />
      </template>
    </Dialog>
  </span>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button, Dialog } from "frappe-ui";
import { getType as getMime } from "mime";
import LucideFileType from "~icons/lucide/file-type";
import LucideFileImage from "~icons/lucide/file-image";
import LucideFileText from "~icons/lucide/file-text";
import LucideFileSpreadsheet from "~icons/lucide/file-spreadsheet";
import LucideFile from "~icons/lucide/file";

interface P {
  label: string;
  url?: string;
}

const props = withDefaults(defineProps<P>(), {
  url: null,
});

const showDialog = ref(false);
const mimeType = getMime(props.label) || "";
const isImage = mimeType.startsWith("image/");
const isPdf = mimeType === "application/pdf";
const isSpreadsheet = mimeType.includes("spreadsheet");
const isText = mimeType === "text/plain";
const isShowable = props.url && (isText || isImage);
const content = ref("");

function getIcon() {
  if (isText) return LucideFileType;
  else if (isImage) return LucideFileImage;
  else if (isPdf) return LucideFileText;
  else if (isSpreadsheet) return LucideFileSpreadsheet;
  else return LucideFile;
}

function toggleDialog() {
  if (!isShowable) return;
  if (isText) {
    fetch(props.url).then((res) => res.text().then((t) => (content.value = t)));
  }
  showDialog.value = !showDialog.value;
}
</script>
