import {
	AlignCenter,
	AlignLeft,
	AlignRight,
	Blockquote,
	Bold,
	BulletList,
	FontColor,
	H1,
	H2,
	H3,
	H4,
	H5,
	H6,
	HorizontalRule,
	InlineCode,
	InsertImage,
	InsertLink,
	InsertTable,
	InsertVideo,
	Italic,
	OrderedList,
	Paragraph,
	Redo,
	Separator,
	TableAddColumnAfter,
	TableAddColumnBefore,
	TableAddRowAfter,
	TableAddRowBefore,
	TableDelete,
	TableDeleteColumn,
	TableDeleteRow,
	TableMergeOrSplit,
	TableToggleHeaderRow,
	Undo,
	type MenuItem,
} from "frappe-ui/editor";
import { ClearFormattingUtility } from "@/utils";

/**
 * v1 editor `MenuItem[]` equivalents of the legacy v0 button-name arrays.
 * Items whose extension isn't loaded hide themselves, so the same list adapts
 * across kits. Headings are exposed as a dropdown group, mirroring the old UI.
 */
const headingGroup: MenuItem = {
	type: "group",
	label: "Heading",
	items: [H2, H3, H4, H5, H6],
};

const alignGroup: MenuItem = {
	type: "group",
	label: "Align",
	items: [AlignLeft, AlignCenter, AlignRight],
};

const tableGroup: MenuItem = {
	type: "group",
	label: "Table",
	items: [
		InsertTable,
		TableAddColumnBefore,
		TableAddColumnAfter,
		TableDeleteColumn,
		TableAddRowBefore,
		TableAddRowAfter,
		TableDeleteRow,
		TableMergeOrSplit,
		TableToggleHeaderRow,
		TableDelete,
	],
};

// Mirrors `textEditorMenuButtons` in @/utils — the rich toolbar used by the
// ticket reply / comment composers and knowledge-base articles.
export const textEditorMenuItems: MenuItem[] = [
	Paragraph,
	headingGroup,
	Separator,
	Bold,
	Italic,
	FontColor,
	Separator,
	alignGroup,
	BulletList,
	OrderedList,
	Separator,
	InsertImage,
	InsertVideo,
	InsertLink,
	Blockquote,
	InlineCode,
	HorizontalRule,
	tableGroup,
	Separator,
	ClearFormattingUtility as unknown as MenuItem,
];

// Mirrors `menuButtons` in @/components/Settings/SavedReplies/savedReplies —
// the saved-reply / compact composer toolbar (adds H1, Undo/Redo).
export const savedReplyMenuItems: MenuItem[] = [
	{ type: "group", label: "Heading", items: [H1, H2, H3, H4, H5, H6] },
	Paragraph,
	Separator,
	Bold,
	Italic,
	Separator,
	BulletList,
	OrderedList,
	Separator,
	AlignLeft,
	AlignCenter,
	AlignRight,
	FontColor,
	Separator,
	InsertImage,
	InsertLink,
	Blockquote,
	InlineCode,
	HorizontalRule,
	tableGroup,
	Separator,
	Undo,
	Redo,
];
