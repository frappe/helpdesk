<template>
  <iframe
    ref="frame"
    :srcdoc="srcdoc"
    class="block h-10 max-h-[500px] w-full max-w-full border-0"
  />
</template>

<script setup lang="ts">
// An iframe keeps the mail's markup and styles out of the portal, as the desk's does.
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { usePreferences } from "@app/stores/preferences";

const props = withDefaults(defineProps<{ content?: string }>(), {
  content: "",
});

const frame = ref<HTMLIFrameElement | null>(null);

const { conversationLayout } = usePreferences();
const isChat = computed(() => conversationLayout.value === "chat");

const QUOTE_SELECTORS = [
  "div.gmail_quote",
  "div#appendonsend",
  "p.reply-to-content",
];

const body = computed(() => collapseQuotes(asHtml(props.content || "")));

// Plain-text mail has no markup, so its newlines would collapse into one paragraph.
function asHtml(content: string) {
  const doc = new DOMParser().parseFromString(content, "text/html");
  if (doc.body.children.length) return content;
  return `<div style="white-space: pre-wrap">${doc.body.innerHTML}</div>`;
}

// The portal's own stylesheets, so prose renders inside the frame as it does outside.
let capturedStyles = "";
function mirroredStyles() {
  if (capturedStyles) return capturedStyles;
  const links = Array.from(
    document.querySelectorAll<HTMLLinkElement>('link[rel="stylesheet"]')
  ).map((link) => `<link rel="stylesheet" href="${link.href}" />`);
  const styles = Array.from(document.querySelectorAll("style")).map(
    (style) => `<style>${style.textContent}</style>`
  );
  capturedStyles = links.join("") + styles.join("");
  return capturedStyles;
}

function collapseQuotes(html: string) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const selector = QUOTE_SELECTORS.find((s) => doc.querySelector(s));
  if (!selector) return html;

  let quote = nextQuote(doc, selector);
  while (quote) {
    fold(doc, quote);
    quote = nextQuote(doc, selector);
  }
  return doc.body.innerHTML;
}

// Folding leaves the matched marker in the document, so skip what is already folded.
function nextQuote(doc: Document, selector: string) {
  return doc.querySelector(`${selector}:not(.replied-content *)`);
}

function fold(doc: Document, quote: Element) {
  const id = `quote-${Math.abs(hash(quote.innerHTML))}`;
  const wrapper = doc.createElement("div");
  wrapper.className = "replied-content";

  const label = doc.createElement("label");
  label.className = "collapse";
  label.setAttribute("for", id);
  label.innerHTML = "...";

  const toggle = doc.createElement("input");
  toggle.id = id;
  toggle.type = "checkbox";

  const hidden = doc.createElement("div");
  hidden.appendChild(quote.cloneNode(true));

  // Whatever follows the quote is part of it.
  let sibling = quote.nextSibling;
  while (sibling) {
    const next = sibling.nextSibling;
    hidden.appendChild(sibling);
    sibling = next;
  }

  wrapper.append(label, toggle, hidden);
  quote.parentElement?.replaceChild(wrapper, quote);
}

// Stable id per quote, so toggling one does not re-render it as a different node.
function hash(value: string) {
  let result = 0;
  for (let i = 0; i < value.length; i++) {
    result = (result << 5) - result + value.charCodeAt(i);
    result |= 0;
  }
  return result;
}

// An iframe inherits no CSS, so the face has to survive until the mirrored sheets load.
const pageStyle = getComputedStyle(document.body);
const contextFont = ref({
  family: pageStyle.fontFamily,
  size: pageStyle.fontSize,
});
onMounted(() => {
  const style = getComputedStyle(frame.value?.parentElement || document.body);
  contextFont.value = { family: style.fontFamily, size: style.fontSize };
});

const srcdoc = computed(
  () => `<!DOCTYPE html><html><head><base target="_blank" />
  ${mirroredStyles()}
  <style>
    body { margin: 0; font-family: ${contextFont.value.family}; font-size: ${
    contextFont.value.size
  }; }
    /* Tailwind's prose caps itself at 65ch; a message uses the width it is given. */
    .email-content { max-width: none; word-break: break-word; }
    .email-content img { margin: 0; border-width: 0; }
    .replied-content .collapse {
      margin: 10px 0;
      cursor: pointer;
      display: flex;
      font-size: larger;
      font-weight: 700;
      height: 12px;
      line-height: 0.1;
      color: var(--ink-gray-8);
      background: var(--surface-gray-2);
      width: 23px;
      justify-content: center;
      border-radius: 5px;
    }
    .replied-content .collapse:hover { background: var(--surface-gray-3); }
    .replied-content .collapse + input { display: none; }
    .replied-content .collapse + input + div { display: none; }
    .replied-content .collapse + input:checked + div { display: block; }
  </style></head><body><div class="email-content prose prose-sm">${
    body.value
  }</div></body></html>`
);

let observer: ResizeObserver | null = null;
let lastWidth = 0;

watch(
  frame,
  (element) => {
    if (!element) return;
    element.onload = () => resize(element);
    // Text re-wraps on a width change, and a height measured at the old width clips it.
    observer?.disconnect();
    observer = new ResizeObserver(([entry]) => {
      const width = entry.contentRect.width;
      if (width === lastWidth) return;
      lastWidth = width;
      resize(element);
    });
    observer.observe(element);
  },
  { immediate: true }
);

onBeforeUnmount(() => observer?.disconnect());

watch(
  [srcdoc, isChat],
  () => frame.value && requestAnimationFrame(() => resize(frame.value!))
);

function resize(element: HTMLIFrameElement) {
  const root = element.contentDocument?.documentElement;
  if (!root) return;
  const fit = () => {
    hug(element);
    element.style.height = `${root.offsetHeight + 1}px`;
  };
  fit();
  element.contentDocument
    ?.querySelectorAll('input[type="checkbox"]')
    .forEach((toggle) => toggle.addEventListener("change", fit));
  // Images and video reserve no space until they arrive, so measure again as each does.
  element.contentDocument?.querySelectorAll("img").forEach((image) => {
    if (!image.complete) image.addEventListener("load", fit);
  });
  element.contentDocument
    ?.querySelectorAll("video")
    .forEach((video) => video.addEventListener("loadedmetadata", fit));
}

// A bubble is as wide as its sentence; an iframe fills whatever it is given instead.
function hug(element: HTMLIFrameElement) {
  // Timeline fills the column instead; the mail centres itself inside it.
  if (!isChat.value) {
    element.style.width = "";
    return;
  }
  const content =
    element.contentDocument?.querySelector<HTMLElement>(".email-content");
  if (!content) return;
  content.style.width = "max-content";
  const natural = Math.ceil(content.getBoundingClientRect().width);
  content.style.width = "";
  if (natural) element.style.width = `${natural}px`;
}
</script>
