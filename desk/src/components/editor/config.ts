import {
  RichTextKit,
  Paragraph,
  HeadingGroup,
  Separator,
  Bold,
  Italic,
  Strike,
  FontColor,
  FontHighlight,
  AlignLeft,
  AlignCenter,
  AlignRight,
  BulletList,
  OrderedList,
  Blockquote,
  InlineCode,
  InsertLink,
  InsertImage,
  InsertVideo,
  InsertTable,
  HorizontalRule,
  commentToolbar,
  type MenuItem,
  type CommandMenuItem,
} from "frappe-ui/editor";
import type { MaybeRefOrGetter } from "vue";
import { CleanStyles, ComponentUtils, HandleExcelPaste } from "@/tiptap-extensions";

/** A mentionable agent as the new editor expects it: `{ id, label }`. */
export interface MentionItem {
  id: string;
  label: string;
}

/**
 * Build the extension list for a Helpdesk rich-text editor.
 *
 * Mentions are passed as a reactive getter so the `@` list stays in sync as
 * agents load (the v0 `:mentions` snapshot prop is what broke suggestions).
 */
export function buildEditorExtensions(options: {
  mentions?: MaybeRefOrGetter<MentionItem[]>;
  extra?: unknown[];
} = {}) {
  const kit = RichTextKit.configure({
    heading: { levels: [2, 3, 4, 5, 6] },
    ...(options.mentions ? { mention: { items: options.mentions } } : {}),
  });
  return [
    kit,
    ComponentUtils,
    HandleExcelPaste,
    CleanStyles,
    ...(options.extra ?? []),
  ];
}

/** Clear-formatting toolbar button (ports the v0 `ClearFormattingUtility`). */
export const ClearFormatting: CommandMenuItem = {
  label: "Clear formatting",
  icon: "lucide-brush-cleaning",
  action: (editor) =>
    editor.chain().focus().unsetAllMarks().clearNodes().cleanStyles().run(),
};

/** Full toolbar mirroring the v0 `textEditorMenuButtons`. */
export const fullToolbar: MenuItem[] = [
  HeadingGroup,
  Separator,
  Bold,
  Italic,
  Strike,
  FontColor,
  FontHighlight,
  Separator,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Separator,
  BulletList,
  OrderedList,
  Blockquote,
  InlineCode,
  Separator,
  InsertLink,
  InsertImage,
  InsertVideo,
  InsertTable,
  HorizontalRule,
  Separator,
  ClearFormatting,
];

/**
 * Curated toolbar for the new-ticket / base editor (ports the v0 `fixedMenu`).
 * Kept compact so the toolbar + Discard/Submit fit on one row.
 */
export const ticketToolbar: MenuItem[] = [
  Paragraph,
  HeadingGroup,
  Separator,
  Bold,
  Italic,
  Separator,
  BulletList,
  OrderedList,
  Separator,
  InsertImage,
  InsertVideo,
  InsertLink,
  Blockquote,
  InlineCode,
  ClearFormatting,
];

/** Compact bubble/inline toolbar for comment display + inline editing. */
export { commentToolbar };
