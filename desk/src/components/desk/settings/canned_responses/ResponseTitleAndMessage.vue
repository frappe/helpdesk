<template>
	<div>
		<div
			v-if="!editable"
			class="flex flex-col space-y-[16px] rounded-[8px] border shadow-sm p-[32px]"
		>
			<div
				class="font-semibold text-[24px] prose prose-p:my-1 border-b pb-[16px] mb-[10px]"
			>
				{{ title }}
			</div>
			<div
				class="overflow-y-auto"
				style="
					min-height: calc(100vh - 500px);
					max-height: calc(100vh - 245px);
				"
				v-html="message"
			></div>
		</div>
		<div v-else>
			<div class="flex flex-col space-y-[16px] h-full">
				<div>
					<Input
						label="Title"
						type="text"
						:value="title"
						@input="
							(val) => {
								tempNewTitle = val
							}
						"
					/>
				</div>
				<div class="flex flex-col">
					<div
						v-if="editMode"
						class="mb-2 block text-sm leading-4 text-gray-700"
					>
						Message
					</div>
					<TextEditor
						:class="editMode ? 'bg-gray-100' : ''"
						ref="textEditor"
						:editor-class="
							!editable
								? 'flex flex-col'
								: editMode
								? 'min-h-[20rem] overflow-y-auto max-h-[73vh] px-3 max-w-full'
								: 'min-h-[20rem] overflow-y-auto max-h-[85vh]'
						"
						:content="message"
						:starterkit-options="{
							heading: { levels: [2, 3, 4, 5, 6] },
						}"
						@change="
							(val) => {
								tempNewMessage = val
							}
						"
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
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { TextEditor } from "frappe-ui"
import { TextEditorFixedMenu } from "frappe-ui/src/components/TextEditor"
import { ref, inject } from "vue"
export default {
	name: "ResponseTitleAndMessage",
	props: ["title", "message", "editable", "responseResource"],
	components: {
		TextEditor,
		TextEditorFixedMenu,
	},
	mounted() {
		this.saveResponseTitleAndMessage = this.save
	},
	watch: {
		tempNewTitle(val) {
			this.updateNewResponseInput({ field: "title", value: val })
		},
		tempNewMessage(val) {
			this.updateNewResponseInput({ field: "message", value: val })
		},
	},
	setup(props) {
		const tempNewTitle = ref(props.title)
		const tempNewMessage = ref(props.message)
		const editMode = inject("editMode")
		const updateNewResponseInput = inject("updateNewResponseInput")
		const saveResponseTitleAndMessage = inject(
			"saveResponseTitleAndMessage"
		)
		return {
			tempNewTitle,
			tempNewMessage,
			editMode,
			updateNewResponseInput,
			saveResponseTitleAndMessage,
		}
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
		save() {
			this.responseResource.setValue.submit({
				title: this.tempNewTitle,
				message: this.tempNewMessage,
			})
			this.editMode = false
		},
	},
}
</script>
