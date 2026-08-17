<template>
  <span>
    <a :href="isShowable ? undefined : url" target="_blank">
      <Button
        :label="label"
        theme="gray"
        variant="outline"
        @click="toggleDialog()"
      >
        <template #prefix>
          <LucidePaperclip class="h-4 w-4" />
        </template>
        <template #suffix>
          <slot name="suffix" />
        </template>
      </Button>
    </a>
    <Dialog v-model:open="showDialog" :title="label" size="4xl">
      <template #default>
        <div
          v-if="isText"
          class="prose prose-sm max-w-none whitespace-pre-wrap"
        >
          {{ content }}
        </div>
        <img v-if="isImage" :src="url" class="m-auto rounded border" />
        <video
          v-if="isVideo"
          :src="url"
          controls
          class="m-auto max-h-[70vh] rounded border"
        />
      </template>
    </Dialog>
  </span>
</template>

<script setup lang="ts">
import { Button, Dialog } from "frappe-ui";
import { getType as getMime } from "mime";
import { ref } from "vue";
import LucidePaperclip from "~icons/lucide/paperclip";

interface P {
  label: string;
  url?: string | null;
}

const props = withDefaults(defineProps<P>(), {
  url: null,
});

const showDialog = ref(false);
const mimeType = getMime(props.label) || "";
const isImage = mimeType.startsWith("image/");
const isVideo = mimeType.startsWith("video/");
const isText = mimeType === "text/plain";
const isShowable = props.url && (isText || isImage || isVideo);
const content = ref("");

function toggleDialog() {
  if (!isShowable) return;
  if (isText) {
    fetch(props.url).then((res) => res.text().then((t) => (content.value = t)));
  }
  showDialog.value = !showDialog.value;
}
</script>
