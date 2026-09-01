<template>
  <iframe
    ref="frame"
    :srcdoc="srcdoc"
    class="block h-10 max-h-[500px] w-full max-w-full border-0"
  />
</template>

<script setup lang="ts">
// Email bodies, rendered the way `desk/src/components/EmailContent.vue` renders
// them: inside an iframe. The iframe is not decoration — it is what keeps a mail's
// own markup and styles from reaching the portal around it, and it is why the desk
// can show the HTML as sent rather than as some editor re-parsed it.
//
// The frame mirrors the page's own stylesheets, the way the desk gives its frame the
// desk bundle: a message written in the editor is prose markup — aligned images, sized
// video, headings, lists, code — and only those rules render it as it was written.
// Inlining a handful of substitutes is what lost the formatting.
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = withDefaults(defineProps<{ content?: string }>(), {
  content: "",
});

const frame = ref<HTMLIFrameElement | null>(null);

/** Gmail, Outlook and helpdesk's own reply markers, in that order. */
const QUOTE_SELECTORS = [
  "div.gmail_quote",
  "div#appendonsend",
  "p.reply-to-content",
];

const body = computed(() => collapseQuotes(asHtml(props.content || "")));

/** Plain-text mail arrives as text with newlines and no markup — rendered as HTML its
 *  line breaks collapse into one paragraph, so it keeps them itself. */
function asHtml(content: string) {
  const doc = new DOMParser().parseFromString(content, "text/html");
  if (doc.body.children.length) return content;
  return `<div style="white-space: pre-wrap">${doc.body.innerHTML}</div>`;
}

/** The page's own stylesheets, mirrored into the frame: link hrefs as links,
 *  vite's injected <style> tags as text. The frame then renders prose exactly as
 *  the portal does — dev and prod alike — with no build path named anywhere.
 *  Captured once per page load: styles do not change under a running page, and a
 *  per-frame capture would re-serialize them for every message in a thread. */
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

// Everything below the first quote marker is folded behind a "..." toggle, so a long
// chain does not bury the message that was actually written.
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

// Folding keeps the quote's own markup, so the marker that matched is still in the
// document afterwards — searching for it again without skipping what is already
// folded finds the copy and folds forever.
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

  // Whatever follows the quote is part of it, so it folds away too.
  let sibling = quote.nextSibling;
  while (sibling) {
    const next = sibling.nextSibling;
    hidden.appendChild(sibling);
    sibling = next;
  }

  wrapper.append(label, toggle, hidden);
  quote.parentElement?.replaceChild(wrapper, quote);
}

/** Stable id per quote, so toggling one does not re-render as a different node. */
function hash(value: string) {
  let result = 0;
  for (let i = 0; i < value.length; i++) {
    result = (result << 5) - result + value.charCodeAt(i);
    result |= 0;
  }
  return result;
}

// An iframe document inherits no CSS from the page, so its body also gets the computed
// font of the spot the frame sits in — the face survives even before the mirrored
// stylesheets finish loading inside the frame.
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

// The frame has no layout of its own, so its height is set from its content — and
// set again when a quote is unfolded.
let observer: ResizeObserver | null = null;
let lastWidth = 0;

watch(
  frame,
  (element) => {
    if (!element) return;
    element.onload = () => resize(element);
    // Text re-wraps whenever the frame changes width — the chat layout gives a message
    // three quarters of the column where the timeline gives it all of one — and a height
    // measured at the old width clips the line that wrapping added.
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
    hug(element);
    element.style.height = `${root.offsetHeight + 1}px`;
  };
  fit();
  element.contentDocument
    ?.querySelectorAll('input[type="checkbox"]')
    .forEach((toggle) => toggle.addEventListener("change", fit));
  // A picture or a recording reserves no space until it has arrived, so the frame is
  // measured again as each one does — otherwise the first frame of a video is all a
  // reader ever sees of it.
  element.contentDocument?.querySelectorAll("img").forEach((image) => {
    if (!image.complete) image.addEventListener("load", fit);
  });
  element.contentDocument
    ?.querySelectorAll("video")
    .forEach((video) => video.addEventListener("loadedmetadata", fit));
}

/** Narrow the frame to what the message actually needs.
 *
 *  A bubble should be as wide as its sentence, and an iframe has no opinion about that —
 *  it fills whatever it is given, which is what made a four-word message as wide as a
 *  paragraph. The content's `max-content` width is that opinion: the width it would take
 *  if nothing wrapped it, measured with nothing wrapping it.
 *
 *  That width is stated in pixels and the cap is left to CSS — the frame's own
 *  `max-width: 100%` inside a card that shrinks to fit and stops at three quarters of the
 *  column. Asking for `min(100%, …)` here instead put the percentage inside the box being
 *  sized from it, and every bubble came out at the same wrong width. */
function hug(element: HTMLIFrameElement) {
  const content =
    element.contentDocument?.querySelector<HTMLElement>(".email-content");
  if (!content) return;
  content.style.width = "max-content";
  const natural = Math.ceil(content.getBoundingClientRect().width);
  content.style.width = "";
  if (natural) element.style.width = `${natural}px`;
}
</script>
