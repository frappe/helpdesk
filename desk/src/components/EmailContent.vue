<template>
  <iframe
    ref="iframeRef"
    :srcdoc="htmlContent"
    class="prose-f block h-10 max-h-[500px] w-full"
  />
</template>

<script setup lang="ts">
import { getFontFamily } from "@/utils";
import { computed, ref, watch } from "vue";

const props = defineProps({
  content: {
    type: String,
    required: true,
  },
});

const iframeRef = ref<HTMLIFrameElement | null>(null);
const _content = ref(props.content);

// Get CSS path - in dev Vite serves it directly, in prod we need the built path
const cssHref = computed(() => {
  if (import.meta.env.DEV) {
    return "/src/index.css";
  }
  // In production, find the built CSS file from the document
  const links = document.querySelectorAll('link[rel="stylesheet"]');
  for (const link of links) {
    const href = link.getAttribute("href");
    if (href?.includes("/assets/helpdesk/desk/") && href.endsWith(".css")) {
      return href;
    }
  }
  // Fallback to a reasonable path
  return "/assets/helpdesk/desk/index.css";
});

const parser = new DOMParser();
const doc = parser.parseFromString(_content.value, "text/html");

const gmailReplyToContent = doc.querySelectorAll("div.gmail_quote");
const outlookReplyToContent = doc.querySelectorAll("div#appendonsend");
const replyToContent = doc.querySelectorAll("p.reply-to-content");

if (gmailReplyToContent.length) {
  _content.value = parseReplyToContent(doc, "div.gmail_quote", true);
} else if (outlookReplyToContent.length) {
  _content.value = parseReplyToContent(doc, "div#appendonsend");
} else if (replyToContent.length) {
  _content.value = parseReplyToContent(doc, "p.reply-to-content");
}

function parseReplyToContent(
  doc: Document,
  selector: string,
  forGmail = false
) {
  function handleAllInstances(doc: Document) {
    const replyToContentElements = doc.querySelectorAll(selector);
    if (replyToContentElements.length === 0) return;
    const replyToContentElement = replyToContentElements[0];
    replaceReplyToContent(replyToContentElement, forGmail);
    handleAllInstances(doc);
  }

  handleAllInstances(doc);
  return doc.body.innerHTML;
}

function replaceReplyToContent(
  replyToContentElement: Element,
  forGmail: boolean
) {
  if (!replyToContentElement) return;
  const randomId = Math.random().toString(36).substring(2, 7);
  const wrapper = doc.createElement("div");
  wrapper.classList.add("replied-content");

  const collapseLabel = doc.createElement("label");
  collapseLabel.classList.add("collapse");
  collapseLabel.setAttribute("for", randomId);
  collapseLabel.innerHTML = "...";
  wrapper.appendChild(collapseLabel);

  const collapseInput = doc.createElement("input");
  collapseInput.setAttribute("id", randomId);
  collapseInput.setAttribute("class", "replyCollapser");
  collapseInput.setAttribute("type", "checkbox");
  wrapper.appendChild(collapseInput);

  if (forGmail) {
    const prevSibling = replyToContentElement.previousElementSibling;
    if (prevSibling && prevSibling.tagName === "BR") {
      prevSibling.remove();
    }
    const cloned = replyToContentElement.cloneNode(true) as Element;
    cloned.classList.remove("gmail_quote");
    wrapper.appendChild(cloned);
  } else {
    const allSiblings = Array.from(
      replyToContentElement.parentElement?.children || []
    );
    const replyToContentIndex = allSiblings.indexOf(replyToContentElement);
    const followingSiblings = allSiblings.slice(replyToContentIndex + 1);

    if (followingSiblings.length === 0) return;

    const clonedFollowingSiblings = followingSiblings.map((sibling) =>
      sibling.cloneNode(true)
    );

    const div = doc.createElement("div");
    div.append(...clonedFollowingSiblings);
    wrapper.append(div);

    for (let i = replyToContentIndex + 1; i < allSiblings.length; i++) {
      replyToContentElement.parentElement?.removeChild(allSiblings[i]);
    }
  }

  replyToContentElement.parentElement?.replaceChild(
    wrapper,
    replyToContentElement
  );
}

const htmlContent = computed(
  () => `
  <!DOCTYPE html>
  <html>
  <head>
    <link rel="stylesheet" href="${cssHref.value}" />
    <base target="_blank" />
    <style>
      :root {
        --bg-surface-gray-3: #ededed;
        --bg-surface-gray-4: #e2e2e2;
      }
      [data-theme='dark'] {
        --bg-surface-gray-3: #343434;
        --bg-surface-gray-4: #424242;
      }
      .replied-content .collapse {
        margin: 10px 0 10px 0;
        visibility: visible;
        cursor: pointer;
        display: flex;
        font-size: larger;
        font-weight: 700;
        height: 12px;
        line-height: 0.1;
        background: #e8eaed;
        width: 23px;
        justify-content: center;
        border-radius: 5px;
      }
      .replied-content .collapse:hover {
        background: #dadce0;
      }
      .replied-content .collapse + input {
        display: none;
      }
      .replied-content .collapse + input + div {
        display: none;
      }
      .replied-content .collapse + input:checked + div {
        display: block;
      }
      .email-content {
        word-break: break-word;
      }
      .email-content :is(:where(table):not(:where([class~='not-prose'], [class~='not-prose'] *))) {
        table-layout: auto;
      }
      .email-content :where(table):not(:where([class~='not-prose'], [class~='not-prose'] *)) {
        width: unset;
        table-layout: auto;
        text-align: unset;
        margin-top: unset;
        margin-bottom: unset;
        font-size: unset;
        line-height: unset;
      }
      .email-content :where(tbody tr):not(:where([class~='not-prose'], [class~='not-prose'] *)) {
        border-bottom-width: 0;
        border-bottom-color: transparent;
      }
      .email-content :is(:where(td):not(:where([class~='not-prose'], [class~='not-prose'] *))) {
        position: unset;
        border-width: 0;
        border-color: transparent;
        padding: 0;
      }
      .email-content :where(tbody td):not(:where([class~='not-prose'], [class~='not-prose'] *)) {
        vertical-align: revert;
      }
      .email-content :is(:where(img):not(:where([class~='not-prose'], [class~='not-prose'] *))) {
        border-width: 0;
      }
      .email-content :where(img):not(:where([class~='not-prose'], [class~='not-prose'] *)) {
        margin: 0;
      }
      .email-content :where(blockquote p:first-of-type):not(:where([class~='not-prose'], [class~='not-prose'] *))::before {
        content: none;
      }
      .email-content :where(blockquote p:last-of-type):not(:where([class~='not-prose'], [class~='not-prose'] *))::after {
        content: none;
      }
    </style>
  </head>
  <body>
    <div dir="auto" class="email-content prose-f">${_content.value}</div>
  </body>
  </html>
  `
);

watch(iframeRef, (iframe) => {
  if (iframe) {
    iframe.onload = () => {
      const emailContent =
        iframe.contentWindow?.document.querySelector(".email-content");
      if (!emailContent) return;

      const parent = emailContent.closest("html");
      if (!parent) return;
      let theme = document.documentElement.getAttribute("data-theme");
      parent.setAttribute("data-theme", theme);

      const font = getFontFamily(_content.value);
      if (font) emailContent.classList.add(font);

      iframe.style.height = parent.offsetHeight + 1 + "px";

      const replyCollapsers = emailContent.querySelectorAll(".replyCollapser");
      if (replyCollapsers.length) {
        replyCollapsers.forEach((replyCollapser) => {
          replyCollapser.addEventListener("change", () => {
            iframe.style.height = parent.offsetHeight + 1 + "px";
          });
        });
      }
    };
  }
});
</script>
