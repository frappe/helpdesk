<template>
	<div class="flex h-full flex-col space-y-[16px]">
		<div>
			<div v-if="editMode" class="flex flex-col">
				<Input
					label="Title"
					type="text"
					:value="article.title"
					@input="onTitleInput"
				/>
				<ErrorMessage :message="articleInputErrors.title" />
			</div>
			<div v-else class="text-[24px] font-semibold">
				{{ article.title }}
			</div>
		</div>
		<div>
			<div class="flex flex-col">
				<div
					v-if="editMode"
					class="mb-2 block text-sm leading-4 text-gray-700"
				>
					Content
				</div>
				<TextEditor
					:class="editMode ? 'bg-gray-100' : ''"
					ref="textEditor"
					:editor-class="
						!editable
							? 'flex flex-col'
							: editMode
							? 'min-h-[20rem] overflow-y-auto max-h-[73vh] w-full px-3'
							: 'min-h-[20rem] overflow-y-auto max-h-[85vh]'
					"
					:content="article.content"
					:starterkit-options="{
						heading: { levels: [2, 3, 4, 5, 6] },
					}"
					@change="onContentInput"
					:editable="editMode"
				>
					<template v-slot:top>
						<div v-if="editMode">
							<TextEditorFixedMenu
								class="m-3 overflow-x-auto"
								:buttons="textEditorMenuButtons"
							/>
						</div>
					</template>
				</TextEditor>
				<ErrorMessage :message="articleInputErrors.content" />
			</div>
		</div>
	</div>
</template>

<script>
// import TextEditor from "@/components/global/TextEditor.vue"
import { ErrorMessage, debounce, TextEditor } from "frappe-ui"
import { TextEditorFixedMenu } from "frappe-ui/src/components/TextEditor"
import { inject } from "vue"

export default {
	name: "ArticleTitleAndContent",
	props: ["article", "editable", "editMode"],
	components: {
		ErrorMessage,
		TextEditor,
		TextEditorFixedMenu,
	},
	setup() {
		const updateArticleTempValues = inject("updateArticleTempValues")
		const articleInputErrors = inject("articleInputErrors")

		return {
			articleInputErrors,
			updateArticleTempValues,
		}
	},
	watch: {
		editMode(val) {
			if (!val) {
				// TODO: can be done in a better way
				this.$refs.textEditor.editor.commands.setContent(
					this.article.content
				)
			}
		},
	},
	computed: {
		textEditorMenuButtons() {
			return [
				"Paragraph",
				[
					"Heading 2",
					"Heading 3",
					"Heading 4",
					"Heading 5",
					"Heading 6",
				],
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
			]
		},
	},
	methods: {
		onTitleInput: debounce(function (value) {
			this.updateArticleTempValues({ field: "title", value })
		}, 300),
		onContentInput: debounce(function (value) {
			this.updateArticleTempValues({ field: "content", value })
		}, 300),
	},
}
</script>
