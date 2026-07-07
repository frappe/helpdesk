import sanitizeHtml from "sanitize-html";

// The inline tags WhatsApp's lightweight markup maps to. Kept deliberately
// small: message bodies are user content rendered with v-html, so the sanitizer
// allowlist is the XSS boundary — nothing here can carry script or attributes.
const ALLOWED_TAGS = ["b", "i", "s", "code", "blockquote", "br", "li"];

// Render WhatsApp-flavoured markup (*bold*, _italic_, ~strike~, `code`, lists)
// to safe HTML. Mirrors the CRM's formatter so the thread reads identically,
// then hard-sanitizes because the result is injected with v-html.
export function formatWhatsAppMessage(message: string | null): string {
  if (!message) return "";

  const html = message
    .replace(/_(.*?)_/g, "<i>$1</i>")
    .replace(/\*(.*?)\*/g, "<b>$1</b>")
    .replace(/~(.*?)~/g, "<s>$1</s>")
    .replace(/```(.*?)```/g, "<code>$1</code>")
    .replace(/`(.*?)`/g, "<code>$1</code>")
    .replace(/^> (.*)$/gm, "<blockquote>$1</blockquote>")
    .replace(/\n/g, "<br>")
    .replace(/\* (.*?)(?=\s*\*|$)/g, "<li>$1</li>")
    .replace(/- (.*?)(?=\s*-|$)/g, "<li>$1</li>")
    .replace(/(\d+)\. (.*?)(?=\s*(\d+)\.|$)/g, "<li>$2</li>");

  return sanitizeHtml(html, {
    allowedTags: ALLOWED_TAGS,
    allowedAttributes: {},
  });
}
