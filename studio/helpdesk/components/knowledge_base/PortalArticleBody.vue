<template>
  <TextEditor
    :content="content"
    :editable="false"
    :extensions="[ComponentUtils]"
    editor-class="prose-v3 max-w-none [&>*:first-child]:mt-0 [&_p+p]:mt-4 [&_:is(h1,h2,h3)]:scroll-mt-4 [&_pre]:overflow-x-auto [&_table]:block [&_table]:overflow-x-auto [&_img]:h-auto [&_img]:max-w-full"
  />
</template>

<script setup lang="ts">
import { TextEditor } from "frappe-ui/experimental";
import { ComponentUtils } from "@helpdesk/shared/tiptap";

withDefaults(defineProps<{ content?: string }>(), { content: "" });
</script>
