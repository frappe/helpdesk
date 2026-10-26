<template>
  <!-- <Editor> renders no element; this div takes the page's classes. -->
  <div>
    <Editor :model-value="content" :extensions="extensions" :editable="false">
      <EditorContent
        :class="`max-w-none [&>*:first-child]:mt-0 [&_p+p]:mt-4 [&_:is(h1,h2,h3,h4,h5,h6)]:scroll-mt-4 [&_pre]:overflow-x-auto ${ARTICLE_IMAGE_CLASSES}`"
      />
    </Editor>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { Extension } from "@tiptap/core";
import type { Node } from "@tiptap/pm/model";
import { Plugin } from "@tiptap/pm/state";
import { Decoration, DecorationSet } from "@tiptap/pm/view";
import { Editor, EditorContent, RichTextKit } from "frappe-ui/editor";
import { ARTICLE_IMAGE_CLASSES, ComponentUtils } from "@helpdesk/shared/tiptap";
import { __ } from "@helpdesk/shared/translation";
import { copyToClipboard, findArticleHeading } from "@helpdesk/shared/utils";

withDefaults(defineProps<{ content?: string }>(), { content: "" });

const router = useRouter();

// Docs-style "#" on each heading: puts its link in the address bar and copies it.
const HeadingAnchors = Extension.create({
  name: "headingAnchors",
  addProseMirrorPlugins() {
    return [
      new Plugin({
        state: {
          init: (_, { doc }) => anchors(doc),
          apply: (tr, old) => (tr.docChanged ? anchors(tr.doc) : old),
        },
        props: {
          decorations(state) {
            return this.getState(state);
          },
        },
      }),
    ];
  },
});

const extensions = [
  RichTextKit.configure({ toc: {} }),
  ComponentUtils,
  HeadingAnchors,
];

function anchors(doc: Node) {
  const widgets: Decoration[] = [];
  doc.descendants((node, pos) => {
    if (node.type.name !== "heading") return true;
    const { id } = node.attrs;
    const text = node.textContent.trim();
    // At the end, so touch screens show it after the text.
    if (id && text)
      widgets.push(
        Decoration.widget(pos + node.nodeSize - 1, () => anchor(id, text), {
          key: id,
          side: 1,
          stopEvent: () => true,
          ignoreSelection: true,
        })
      );
    return false;
  });
  return DecorationSet.create(doc, widgets);
}

// The "#" is CSS, so heading text (the legacy-id fallback, selections) stays clean.
function anchor(id: string, text: string) {
  const link = document.createElement("a");
  link.href = `#${id}`;
  link.className = "heading-anchor";
  link.setAttribute("aria-label", __("Copy link to {0}", [text]));
  link.addEventListener("click", (event) => {
    // Modified clicks open the link in a new tab or window, as usual.
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
      return;
    event.preventDefault();
    copyHeadingLink(id);
  });
  return link;
}

// Replace, not push: copying a link shouldn't add Back steps.
// No query string, so the copied link is the article path plus the heading.
async function copyHeadingLink(id: string) {
  findArticleHeading(id)?.scrollIntoView({ block: "start" });
  await router.replace({ hash: `#${id}` });
  await copyToClipboard(location.href, __("Link copied"));
}
</script>

<style>
.ProseMirror :is(h1, h2, h3, h4, h5, h6):has(> .heading-anchor) {
  position: relative;
}
.ProseMirror .heading-anchor {
  border: 0;
  font-weight: 400;
  color: var(--ink-gray-5);
  text-decoration: none;
}
.ProseMirror .heading-anchor::before {
  content: "#";
  border-bottom: 1px solid var(--ink-gray-4);
}
.ProseMirror .heading-anchor:hover {
  color: var(--ink-gray-8);
}
.ProseMirror .heading-anchor:hover::before {
  border-bottom-color: var(--ink-gray-6);
}
.ProseMirror .heading-anchor:focus-visible {
  outline: none;
}
.ProseMirror .heading-anchor:focus-visible::before {
  border-radius: 2px;
  box-shadow: 0 0 0 2px var(--outline-gray-5);
}
/* Mouse: hangs in the left gutter by the first line and shows on hover, like
   the docs. The padding bridges the gap, so the pointer keeps the hover. */
@media (hover: hover) and (min-width: 640px) {
  .ProseMirror .heading-anchor {
    position: absolute;
    top: 0;
    inset-inline-end: 100%;
    padding-inline-end: 0.5rem;
    opacity: 0;
    transition: opacity 0.15s ease;
  }
  .ProseMirror :is(h1, h2, h3, h4, h5, h6):hover > .heading-anchor,
  .ProseMirror .heading-anchor:focus-visible {
    opacity: 1;
  }
}
/* Touch has no hover, and below sm the 16px gutter clips it: after the text. */
@media (hover: none), (max-width: 639.98px) {
  .ProseMirror .heading-anchor {
    margin-inline-start: 0.375em;
  }
}
@media print {
  .ProseMirror .heading-anchor {
    display: none;
  }
}
</style>
