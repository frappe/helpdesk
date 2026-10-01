<template>
  <TextEditor
    :content="content"
    :editable="false"
    :extensions="[ComponentUtils]"
    editor-class="prose-sm max-w-none [&_:is(h1,h2,h3)]:scroll-mt-4"
  />
</template>

<script setup lang="ts">
// The editor the desk writes articles in, read-only, so they read as written.
import { TextEditor } from "frappe-ui/experimental";
import { ComponentUtils } from "@helpdesk/shared/tiptap";

withDefaults(defineProps<{ content?: string }>(), { content: "" });
</script>
