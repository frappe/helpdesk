<template>
  <iframe
    ref="frame"
    :srcdoc="srcdoc"
    sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox"
    referrerpolicy="no-referrer"
    class="block h-10 max-h-[500px] w-full max-w-full border-0"
  />
</template>

<script setup lang="ts">
// An iframe keeps the mail's markup and styles out of the portal, as the desk's does.
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  applyCssToIframe,
  stripEmailColors,
} from "@framework/ui/components/ActivityTimeline/utils";

const QUOTE_SELECTORS = [
  "div.gmail_quote",
  "div#appendonsend",
  "p.reply-to-content",
];

const props = withDefaults(
  defineProps<{ content?: string; isChat?: boolean }>(),
  { content: "", isChat: false }
);

const frame = ref<HTMLIFrameElement | null>(null);

const body = computed(() =>
  collapseQuotes(asHtml(stripEmailColors(props.content || "")))
);

// Plain-text mail has no markup, so its newlines would collapse into one paragraph.
function asHtml(content: string) {
  const doc = new DOMParser().parseFromString(content, "text/html");
  if (doc.body.children.length) return content;
  return `<div class="whitespace-pre-wrap">${doc.body.innerHTML}</div>`;
}

function collapseQuotes(html: string) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  stripActiveContent(doc);
  const selector = QUOTE_SELECTORS.find((s) => doc.querySelector(s));
  if (!selector) return doc.body.innerHTML;

  let quote = nextQuote(doc, selector);
  while (quote) {
    fold(doc, quote);
    quote = nextQuote(doc, selector);
  }
  return doc.body.innerHTML;
}

// Scripts and handlers go at parse time; the sandbox and CSP stay as the runtime backstop.
function stripActiveContent(doc: Document) {
  doc.querySelectorAll("script").forEach((element) => element.remove());
  doc.querySelectorAll("*").forEach((element) => {
    for (const attribute of [...element.attributes]) {
      if (attribute.name.toLowerCase().startsWith("on"))
        element.removeAttribute(attribute.name);
    }
  });
}

// Folding leaves the matched marker in the document, so skip what is already folded.
function nextQuote(doc: Document, selector: string) {
  return doc.querySelector(`${selector}:not(.replied-content *)`);
}

function fold(doc: Document, quote: Element) {
  const id = `quote-${Math.abs(hash(quote.innerHTML))}`;
  const wrapper = doc.createElement("div");
  wrapper.className = "replied-content";

  // Literal classes: the frame mirrors the page's sheets, and Tailwind scans this file.
  const label = doc.createElement("label");
  label.className =
    "my-2.5 flex h-3 w-[23px] cursor-pointer items-center justify-center rounded-5 bg-surface-gray-2 text-lg font-bold leading-none text-ink-gray-8 hover:bg-surface-gray-3";
  label.setAttribute("for", id);
  label.innerHTML = "...";

  const toggle = doc.createElement("input");
  toggle.id = id;
  toggle.type = "checkbox";
  toggle.className = "peer hidden";

  const hidden = doc.createElement("div");
  hidden.className = "hidden peer-checked:block";
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

// Inline, not a class: the face is a runtime value read off the page.
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
  () => `<!DOCTYPE html><html><head>
  <meta http-equiv="Content-Security-Policy" content="script-src 'none'; object-src 'none';" />
  <base target="_blank" />
  </head><body class="m-0" style="font-family: ${contextFont.value.family}; font-size: ${contextFont.value.size}">
  <div class="email-content prose prose-sm max-w-none break-words prose-img:m-0 prose-img:border-0">${body.value}</div>
  </body></html>`
);

let observer: ResizeObserver | null = null;
let lastWidth = 0;

watch(
  frame,
  (element) => {
    if (!element) return;
    element.onload = () => {
      // The portal's own sheets, so prose renders inside the frame as it does outside.
      applyCssToIframe(element, () => resize(element));
      resize(element);
    };
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
  [srcdoc, () => props.isChat],
  () => frame.value && requestAnimationFrame(() => resize(frame.value!))
);

function resize(element: HTMLIFrameElement) {
  const root = element.contentDocument?.documentElement;
  if (!root) return;
  const fit = () => {
    fitFrameToContent(element);
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
function fitFrameToContent(element: HTMLIFrameElement) {
  // Timeline fills the column instead; the mail centres itself inside it.
  if (!props.isChat) {
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
