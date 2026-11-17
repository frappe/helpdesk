const URL_PATTERN = /(https?:\/\/[^\s<>"]+)/g;

// WhatsApp's own markup; `_` needs a word boundary so snake_case stays as is
const RULES: Array<[RegExp, string]> = [
  [/```([\s\S]+?)```/g, "<code>$1</code>"],
  [/`([^`\n]+)`/g, "<code>$1</code>"],
  [/\*([^*\n]+)\*/g, "<b>$1</b>"],
  [/(^|\W)_([^_\n]+)_(?=\W|$)/g, "$1<i>$2</i>"],
  [/~([^~\n]+)~/g, "<s>$1</s>"],
  [/\n/g, "<br>"],
];

/** Render WhatsApp text as safe HTML: escaped first, then bold, italic, strike, code and links. */
export function formatWhatsAppText(text: string | null | undefined): string {
  return (text ?? "")
    .split(URL_PATTERN)
    .map((part, index) => (index % 2 ? link(part) : markup(part)))
    .join("");
}

function markup(text: string): string {
  return RULES.reduce(
    (html, [pattern, replacement]) => html.replace(pattern, replacement),
    escapeHtml(text)
  );
}

function link(url: string): string {
  const safe = escapeHtml(url);
  return `<a href="${safe}" target="_blank" rel="noopener noreferrer" class="underline">${safe}</a>`;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
