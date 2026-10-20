<template>
  <iframe
    ref="frame"
    :srcdoc="srcdoc"
    sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox"
    referrerpolicy="no-referrer"
    class="email-fade block h-10 max-h-[500px] w-full max-w-full border-0"
  />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { __ } from "@helpdesk/shared/translation";
import {
  applyCssToIframe,
  bottomFade,
  stripEmailColors,
  useDataTheme,
} from "@framework/ui/components/ActivityTimeline/utils";

const QUOTE_SELECTORS = [
  "div.gmail_quote",
  "div#appendonsend",
  "p.reply-to-content",
];

const props = withDefaults(defineProps<{ content?: string }>(), {
  content: "",
});

const frame = ref<HTMLIFrameElement | null>(null);

const body = computed(() =>
  collapseQuotes(stripEmailColors(props.content || ""))
);

function collapseQuotes(html: string) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  stripActiveContent(doc);
  trimEmptyEdges(doc);
  const selector = QUOTE_SELECTORS.find((s) => doc.querySelector(s));
  if (!selector) return doc.body.innerHTML;

  let quote = nextQuote(doc, selector);
  while (quote) {
    fold(doc, quote);
    quote = nextQuote(doc, selector);
  }
  return doc.body.innerHTML;
}

// Strip scripts at parse time; sandbox and CSP are the backstop.
// `javascript:` links open in an unsandboxed popup with this origin.
const SCRIPT_URL = /^(javascript|vbscript):/i;

function stripActiveContent(doc: Document) {
  doc.querySelectorAll("script").forEach((element) => element.remove());
  doc.querySelectorAll("*").forEach((element) => {
    for (const attribute of [...element.attributes]) {
      const name = attribute.name.toLowerCase();
      // Browsers ignore whitespace and control chars in a URL scheme.
      const url = attribute.value.replace(/[\u0000-\u0020]/g, "");
      if (name.startsWith("on") || SCRIPT_URL.test(url))
        element.removeAttribute(attribute.name);
    }
  });
}

// The editor's trailing empty paragraph would pad short bubbles.
function trimEmptyEdges(doc: Document) {
  const isEmpty = (node: ChildNode | null) =>
    !!node &&
    (node.nodeType === Node.TEXT_NODE
      ? !node.textContent?.trim()
      : ["P", "BR", "DIV"].includes(node.nodeName) &&
        !(node as Element).querySelector("img, video, iframe") &&
        !node.textContent?.trim());
  while (isEmpty(doc.body.lastChild)) doc.body.lastChild!.remove();
  while (isEmpty(doc.body.firstChild)) doc.body.firstChild!.remove();
}

// The folded marker stays in the doc; skip already-folded quotes.
function nextQuote(doc: Document, selector: string) {
  return doc.querySelector(`${selector}:not(.replied-content *)`);
}

function fold(doc: Document, quote: Element) {
  const id = `quote-${Math.abs(hash(quote.innerHTML))}`;
  const wrapper = doc.createElement("div");
  wrapper.className = "replied-content";

  // Literal classes: Tailwind scans this file for the frame's sheets.
  const label = doc.createElement("label");
  label.className =
    "mt-2 flex h-4 w-6 cursor-pointer items-center justify-center gap-[2px] rounded-full bg-surface-gray-3 text-ink-gray-7 hover:bg-surface-gray-4";
  label.setAttribute("for", id);
  label.setAttribute("title", __("Show quoted text"));
  // Drawn dots, not "...": text sits on its baseline, below the pill's centre.
  label.innerHTML =
    '<span class="size-[3px] rounded-full bg-current"></span>'.repeat(3);

  const toggle = doc.createElement("input");
  toggle.id = id;
  toggle.type = "checkbox";
  toggle.className = "peer hidden";

  const hidden = doc.createElement("div");
  hidden.className = "hidden peer-checked:block";
  hidden.appendChild(quote.cloneNode(true));

  let sibling = quote.nextSibling;
  while (sibling) {
    const next = sibling.nextSibling;
    hidden.appendChild(sibling);
    sibling = next;
  }

  wrapper.append(label, toggle, hidden);
  quote.parentElement?.replaceChild(wrapper, quote);
}

// Stable id per quote across re-renders.
function hash(value: string) {
  let result = 0;
  for (let i = 0; i < value.length; i++) {
    result = (result << 5) - result + value.charCodeAt(i);
    result |= 0;
  }
  return result;
}

// Read once: a reactive theme in srcdoc would reload the frame.
const dataTheme = useDataTheme();
const initialTheme = dataTheme.value;

const srcdoc = computed(
  () => `<!DOCTYPE html><html data-theme="${initialTheme}"><head>
  <meta http-equiv="Content-Security-Policy" content="script-src 'none'; object-src 'none';" />
  <base target="_blank" />
  <style>:root { color-scheme: light; } [data-theme='dark'] { color-scheme: dark; } html, body { background: transparent; }
  .email-content pre { background: var(--surface-gray-3); color: var(--ink-gray-8); }
  .email-content table { display: block; max-width: 100%; overflow-x: auto; }
  .email-content :is(th, td) { padding: 4px 12px; }</style>
  </head><body class="m-0">
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
      applyCssToIframe(element, () => resize(element));
      resize(element);
      element.contentWindow?.addEventListener(
        "scroll",
        () => syncFade(element),
        { passive: true }
      );
    };
    // Re-measure on width change, or rewrapped text clips.
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
  srcdoc,
  () => frame.value && requestAnimationFrame(() => resize(frame.value!))
);

function resize(element: HTMLIFrameElement) {
  const root = element.contentDocument?.documentElement;
  if (!root) return;
  const fit = () => {
    fitFrameToContent(element);
    element.style.height = `${root.offsetHeight + 1}px`;
    syncFade(element);
  };
  fit();
  element.contentDocument?.fonts?.ready.then(fit);
  element.contentDocument
    ?.querySelectorAll('input[type="checkbox"]')
    .forEach((toggle) => toggle.addEventListener("change", fit));
  // Media reserve no space until loaded; re-measure then.
  element.contentDocument?.querySelectorAll("img").forEach((image) => {
    if (!image.complete) image.addEventListener("load", fit);
  });
  element.contentDocument
    ?.querySelectorAll("video")
    .forEach((video) => video.addEventListener("loadedmetadata", fit));
}

// Fade the bottom edge while more of a capped email remains below.
function syncFade(element: HTMLIFrameElement) {
  const root = element.contentDocument?.documentElement;
  if (root) element.style.setProperty("--fade", bottomFade(root));
}

// Size the bubble to its text; an iframe fills its container.
function fitFrameToContent(element: HTMLIFrameElement) {
  const content =
    element.contentDocument?.querySelector<HTMLElement>(".email-content");
  if (!content) return;
  content.style.width = "max-content";
  const natural = Math.ceil(content.getBoundingClientRect().width);
  content.style.width = "";
  if (natural) element.style.width = `${natural}px`;
}

watch(dataTheme, (theme) =>
  frame.value?.contentDocument?.documentElement.setAttribute(
    "data-theme",
    theme
  )
);
</script>

<style scoped>
/* At 0px the stop sits on the edge, so the mask is opaque. */
.email-fade {
  mask-image: linear-gradient(
    to bottom,
    #000 calc(100% - var(--fade, 0px)),
    transparent
  );
}
</style>
