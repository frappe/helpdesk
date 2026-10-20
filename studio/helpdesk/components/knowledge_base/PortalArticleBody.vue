<template>
  <!-- <Editor> renders no element; this div takes the page's classes. -->
  <div>
    <Editor :model-value="content" :extensions="extensions" :editable="false">
      <EditorContent
        :class="`max-w-none [&>*:first-child]:mt-0 [&_p+p]:mt-4 [&_:is(h1,h2,h3)]:scroll-mt-4 [&_pre]:overflow-x-auto ${ARTICLE_IMAGE_CLASSES}`"
      />
    </Editor>
  </div>
</template>

<script setup lang="ts">
import { Editor, EditorContent, RichTextKit } from "frappe-ui/editor";
import { ARTICLE_IMAGE_CLASSES, ComponentUtils } from "@helpdesk/shared/tiptap";

withDefaults(defineProps<{ content?: string }>(), { content: "" });

const extensions = [RichTextKit.configure({ toc: {} }), ComponentUtils];
</script>
