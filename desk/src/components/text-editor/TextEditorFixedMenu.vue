<template>
	<TextEditorFixedMenu :buttons="MENU_BUTTONS" />
</template>
<script setup lang="ts">
import { TextEditorFixedMenu } from "frappe-ui";

const MENU_BUTTONS = [
	"Paragraph",
	["Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"],
	"Separator",
	"Bold",
	"Italic",
	"Separator",
	"Bullet List",
	"Numbered List",
	"Separator",
	"Align Left",
	"Align Center",
	"Align Right",
	"Separator",
	"Image",
	"Video",
	"Link",
	"Blockquote",
	"Code",
	"Horizontal Rule",
	[
		"InsertTable",
		"AddColumnBefore",
		"AddColumnAfter",
		"DeleteColumn",
		"AddRowBefore",
		"AddRowAfter",
		"DeleteRow",
		"MergeCells",
		"SplitCell",
		"ToggleHeaderColumn",
		"ToggleHeaderRow",
		"ToggleHeaderCell",
		"DeleteTable",
	],
	"Separator",
	"Undo",
	"Redo",
];
</script>
