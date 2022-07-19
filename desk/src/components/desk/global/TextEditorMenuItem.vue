<template>
	<div>
		<div>
			<div class="h-4 border-r w-2" v-if="item=='|'"></div>
			<div v-else-if="item=='file-upload'" class="hover:bg-gray-50 rounded h-[20px] w-[20px] p-[2px]">
				<FileUploader @success="(file) => attachments.push(file)">
					<template v-slot="{ progress, uploading, openFileSelector }">
						<FeatherIcon name="paperclip" class="h-[17px]" @click="openFileSelector" role="button" :disabled="uploading" />
					</template>
				</FileUploader>
			</div>
			<a v-else-if="commands[item] && editor" :title="commands[item].label">
				<CustomIcons 
					@click="commands[item].action(editor)" 
					:class="commands[item].isActive && commands[item].isActive(editor) ? 'bg-blue-50 border-blue-500 border' : ''" 
					role="button" 
					:name="commands[item].icon" 
					class="h-5 w-5 rounded hover:bg-gray-50" 
				/>
			</a>
		</div>
	</div>
</template>

<script>
import CustomIcons from './CustomIcons.vue'
import { FileUploader, FeatherIcon } from 'frappe-ui'
import { ref } from 'vue'

export default {
	name: 'TextEditorMenuItem',
	props: ['item', 'editor', 'attachments'],
	components: {
		CustomIcons,
		FileUploader,
		FeatherIcon
	},
	setup() {
		const commands = ref({})

		return {
			commands
		}
	},
	mounted() {
		this.commands = {
			bold: {
				label: 'Bold',
				icon: 'bold',
				action: (editor) => editor.chain().focus().toggleBold().run(),
    			isActive: (editor) => editor.isActive('bold'),
			},
			italic: {
				label: 'Italic',
				icon: 'italic',
				action: (editor) => editor.chain().focus().toggleItalic().run(),
    			isActive: (editor) => editor.isActive('italic'),
			},
			underline: {
				label: 'Underline',
				icon: 'underline',
				action: (editor) => editor.chain().focus().toggleUnderline().run(),
    			isActive: (editor) => editor.isActive('underline'),
			},
			quote: {
				label: 'Quote',
				icon: 'quote',
				action: (editor) => editor.chain().focus().toggleBlockquote().run(),
    			isActive: (editor) => editor.isActive('blockquote'),
			},
			code: {
				label: 'Code',
				icon: 'code',
				action: (editor) => editor.chain().focus().toggleCodeBlock().run(),
    			isActive: (editor) => editor.isActive('codeBlock'),
			},
			'link-url': {
				label: 'Link',
				icon: 'link-url',
				action: (editor) => editor.chain().focus().toggleLink().run(),
    			isActive: (editor) => editor.isActive('link'),
			},
			'numbered-list': {
				label: 'Numbered List',
				icon: 'numbered-list',
				action: (editor) => editor.chain().focus().toggleOrderedList().run(),
    			isActive: (editor) => editor.isActive('orderedList'),
			},
			'bullet-list': {
				label: 'Bullet List',
				icon: 'bullet-list',
				action: (editor) => editor.chain().focus().toggleBulletList().run(),
    			isActive: (editor) => editor.isActive('bulletList'),
			},
			'left-align': {
				label: 'Left Align',
				icon: 'left-align',
				action: (editor) => editor.chain().focus().setTextAlign('left').run(),
    			isActive: (editor) => editor.isActive({ textAlign: 'left' }),
			},
			'clear-formatting': {
				label: 'Clear Formatting',
				icon: 'clear-formatting',
				action: (editor) => editor.chain().focus().clearNodes().unsetAllMarks()
			},
		}
	}
}
</script>