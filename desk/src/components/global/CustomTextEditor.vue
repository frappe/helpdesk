<template>
	<div v-if="show">
		<slot name="main">
			<slot v-if="editor" name="top-section" :editor="editor"></slot>
			<div @click="editor?.commands.focus()">
				<TextEditor
					ref="textEditor"
					class="overflow-y-scroll cursor-text h-full"
					:class="editorClasses"
					:content="content"
					:editor-class="editorClasses"
					:placeholder="placeholder"
					:editable="true"
					:extensions="[CustomHardBreakExtention]"
					:mentions="mentions"
					@change="
						(val) => {
							content = val
							this.$emit('change', val)
						}
					"
				/>
			</div>
			<slot v-if="editor" name="bottom-section" :editor="editor"></slot>
		</slot>
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
import { TextEditor } from "frappe-ui"
import { HardBreak } from "@tiptap/extension-hard-break"
import { ref, computed, nextTick } from "vue"

export default {
	name: "CustomTextEditor",
	props: ["content", "placeholder", "editorClasses", "show", "mentions"],
	emits: ["change"],
	components: {
		TextEditor,
	},
	setup() {
		const textEditor = ref(null)
		const editor = computed(() => {
			return textEditor.value?.editor || null
		})
		const focusEditor = () => {
			nextTick(() => {
				editor.value?.commands.focus()
			})
		}

		const setLinkDialog = ref({ url: "", show: false })
		const insertLink = () => {
			setLinkDialog.value.show = true
			let existingURL = editor.value?.getAttributes("link").href
			if (existingURL) {
				setLinkDialog.value.url = existingURL
			}
		}
		const setLink = (url) => {
			// empty
			if (url === "") {
				editor.value
					?.chain()
					.focus()
					.extendMarkRange("link")
					.unsetLink()
					.run()
			} else {
				// update link
				editor.value
					?.chain()
					.focus()
					.extendMarkRange("link")
					.setLink({ href: url })
					.run()
			}

			setLinkDialog.value.show = false
			setLinkDialog.value.url = ""
		}

		return {
			textEditor,
			setLinkDialog,
			insertLink,
			setLink,
			focusEditor,
			editor,
		}
	},
	computed: {
		CustomHardBreakExtention() {
			return HardBreak.extend({
				addKeyboardShortcuts() {
					return {
						Enter: () => this.editor.commands.setHardBreak(),
					}
				},
			})
		},
	},
}
</script>
