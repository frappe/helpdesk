<template>
	<div>
		<div>
			<div class="h-4 border-r" v-if="item == '|'"></div>
			<div
				v-else-if="item == 'file-upload'"
				class="hover:bg-gray-200 rounded h-[20px] w-[20px] p-[2px]"
			>
				<FileUploader @success="(file) => attachments.push(file)">
					<template
						v-slot="{ progress, uploading, openFileSelector }"
					>
						<FeatherIcon
							name="paperclip"
							class="h-[17px]"
							@click="openFileSelector"
							role="button"
							:disabled="uploading"
						/>
					</template>
				</FileUploader>
			</div>
			<a
				v-else-if="commands[item] && editor"
				:title="commands[item].label"
			>
				<CustomIcons
					@click="commands[item].action(editor)"
					:class="
						commands[item].isActive &&
						commands[item].isActive(editor)
							? 'bg-gray-200'
							: ''
					"
					role="button"
					:name="commands[item].icon"
					class="h-6 w-6 p-0.5 rounded hover:bg-gray-200"
				/>
			</a>
		</div>
		<Dialog :options="{ title: 'Set Link' }" v-model="setLinkDialog.show">
			<template #body-content>
				<Input
					type="text"
					label="URL"
					v-model="setLinkDialog.url"
					@keydown.enter="(e) => setLink(e.target.value)"
				/>
			</template>
			<template #actions>
				<Button
					appearance="primary"
					@click="setLink(setLinkDialog.url)"
				>
					Save
				</Button>
			</template>
		</Dialog>
	</div>
</template>

<script>
import CustomIcons from "../desk/global/CustomIcons.vue"
import { FileUploader, FeatherIcon } from "frappe-ui"
import { ref } from "vue"

export default {
	name: "TextEditorMenuItem",
	props: ["item", "editor", "attachments"],
	data() {
		return {
			setLinkDialog: { url: "", show: false },
		}
	},
	components: {
		CustomIcons,
		FileUploader,
		FeatherIcon,
	},
	setup() {
		const commands = ref({})

		return {
			commands,
		}
	},
	mounted() {
		this.commands = {
			bold: {
				label: "Bold",
				icon: "bold",
				action: (editor) => editor.chain().focus().toggleBold().run(),
				isActive: (editor) => editor.isActive("bold"),
			},
			italic: {
				label: "Italic",
				icon: "italic",
				action: (editor) => editor.chain().focus().toggleItalic().run(),
				isActive: (editor) => editor.isActive("italic"),
			},
			underline: {
				label: "Underline",
				icon: "underline",
				action: (editor) =>
					editor.chain().focus().toggleUnderline().run(),
				isActive: (editor) => editor.isActive("underline"),
			},
			quote: {
				label: "Quote",
				icon: "quote",
				action: (editor) =>
					editor.chain().focus().toggleBlockquote().run(),
				isActive: (editor) => editor.isActive("blockquote"),
			},
			code: {
				label: "Code",
				icon: "code",
				action: (editor) =>
					editor.chain().focus().toggleCodeBlock().run(),
				isActive: (editor) => editor.isActive("codeBlock"),
			},
			"link-url": {
				label: "Link",
				icon: "link-url",
				action: (editor) => {
					this.setLinkDialog.show = true
					let existingURL = editor.getAttributes("link").href
					if (existingURL) {
						this.setLinkDialog.url = existingURL
					}
				},
				isActive: (editor) => editor.isActive("link"),
			},
			"numbered-list": {
				label: "Numbered List",
				icon: "numbered-list",
				action: (editor) =>
					editor.chain().focus().toggleOrderedList().run(),
				isActive: (editor) => editor.isActive("orderedList"),
			},
			"bullet-list": {
				label: "Bullet List",
				icon: "bullet-list",
				action: (editor) =>
					editor.chain().focus().toggleBulletList().run(),
				isActive: (editor) => editor.isActive("bulletList"),
			},
			"left-align": {
				label: "Left Align",
				icon: "left-align",
				action: (editor) =>
					editor.chain().focus().setTextAlign("left").run(),
				isActive: (editor) => editor.isActive({ textAlign: "left" }),
			},
			"right-align": {
				label: "Right Align",
				icon: "right-align",
				action: (editor) =>
					editor.chain().focus().setTextAlign("right").run(),
				isActive: (editor) => editor.isActive({ textAlign: "right" }),
			},
			"center-align": {
				label: "Center Align",
				icon: "center-align",
				action: (editor) =>
					editor.chain().focus().setTextAlign("center").run(),
				isActive: (editor) => editor.isActive({ textAlign: "center" }),
			},
			"clear-formatting": {
				label: "Clear Formatting",
				icon: "clear-formatting",
				action: (editor) =>
					editor.chain().focus().clearNodes().unsetAllMarks(),
			},
		}
	},
	methods: {
		setLink(url) {
			// empty
			if (url === "") {
				this.editor
					.chain()
					.focus()
					.extendMarkRange("link")
					.unsetLink()
					.run()
			} else {
				// update link
				this.editor
					.chain()
					.focus()
					.extendMarkRange("link")
					.setLink({ href: url })
					.run()
			}

			this.setLinkDialog.show = false
			this.setLinkDialog.url = ""
		},
	},
}
</script>
