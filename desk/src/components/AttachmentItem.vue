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
          <Icon :icon="getIcon()" />
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
import { Icon } from "@iconify/vue";

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
  if (isText) return "lucide:file-type";
  else if (isImage) return "lucide:file-image";
  else if (isPdf) return "lucide:file-text";
  else if (isSpreadsheet) return "lucide:file-spreadsheet";
  else return "lucide:file";
}

function toggleDialog() {
  if (!isShowable) return;
  if (isText) {
    fetch(props.url).then((res) => res.text().then((t) => (content.value = t)));
  }
  showDialog.value = !showDialog.value;
}
</script>
