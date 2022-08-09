<template>
	<div>
		<div v-if="!editable && !isNew" class="flex flex-col space-y-[16px]">
			<div class="font-semibold text-[24px] prose prose-p:my-1"> {{ title }} </div>
			<div v-html="content"></div>
		</div>
		<div v-else>
			<div class="flex flex-col space-y-[16px] h-full">
				<Input label="Title" type="text" :value="title" @input="(val) => { tempNewTitle = val }"/>
				<CustomTextEditor 
					:show="true"
					ref="contentEditor"
					@click="$refs.contentEditor.focusEditor()"
					:content="content" 
					@change="(val) => { tempNewContent = val }"
					editorClasses="w-full p-[12px] bg-gray-100 min-h-[180px] max-h-[300px]"
					class="rounded-[8px]"
				>
					<template #top-section="{ editor }">
						<div class="flex flex-col">
							<div class="block mb-2 text-sm leading-4 text-gray-700">Article</div>
							<div class="flex flex-row items-center space-x-1.5 p-1.5 rounded-t-[8px] border bg-gray-50">
								<div v-for="item in [
									'bold', 'italic', '|',
									'quote', 'code', '|',
									'numbered-list', 'bullet-list', 'left-align', 'center-align', 'right-align'
								]" :key="item">
									<TextEditorMenuItem :item="item" :editor="editor" />
								</div>
							</div>
						</div>
					</template>
				</CustomTextEditor>
			</div>
		</div>
	</div>
</template>

<script>
import CustomTextEditor from '@/components/global/CustomTextEditor.vue'
import TextEditorMenuItem from '@/components/global/TextEditorMenuItem.vue'
import { ref, inject } from 'vue'

export default {
	name: 'ArticleTitleAndContent',
	props: ['title', 'content', 'editable', 'articleResource', 'isNew'],
	components: {
		CustomTextEditor,
		TextEditorMenuItem
	},
	mounted() {
		this.$event.on('save_current_article', (publish=false) => {
			this.save(publish)
		})

		this.saveArticleTitleAndContent = this.save
	},
	unmounted() {
		this.$event.off('save_current_article')
	},
	watch: {
		tempNewTitle(val) {
			if (this.isNew) {
				this.updateNewArticleInput({ field: 'title', value: val })
			}
		},
		tempNewContent(val) {
			if (this.isNew) {
				this.updateNewArticleInput({ field: 'content', value: val })
			}
		}
	},
	setup(props) {
		const tempNewTitle = ref(props.title)
		const tempNewContent = ref(props.content)

		const editMode = inject('editMode')
		const updateNewArticleInput = inject('updateNewArticleInput')

		const saveArticleTitleAndContent = inject('saveArticleTitleAndContent')

		return {
			tempNewTitle,
			tempNewContent,
			editMode,
			updateNewArticleInput,
			saveArticleTitleAndContent
		}
	},
	methods: {
		save(publish=false) {
			this.articleResource.setValue.submit({
				title: this.tempNewTitle, 
				content: this.tempNewContent, 
				published: publish
			})
			this.editMode = false
		}
	}
}
</script>