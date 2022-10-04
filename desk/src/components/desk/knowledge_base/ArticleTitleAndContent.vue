<template>
	<div>
		<div
			v-if="!editable && !isNew"
			class="flex flex-col space-y-[16px] rounded-[8px] border shadow-sm p-[32px]"
		>
			<div
				class="font-semibold text-[24px] prose prose-p:my-1 border-b pb-[16px] mb-[10px]"
			>
				{{ title }}
			</div>
			<div
				class="overflow-y-scroll"
				style="
					min-height: calc(100vh - 500px);
					max-height: calc(100vh - 245px);
				"
				v-html="content"
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
					<ErrorMessage :message="articleInputErrors.title" />
				</div>
				<div>
					<CustomTextEditor
						:show="true"
						ref="contentEditor"
						@click="$refs.contentEditor.focusEditor()"
						:content="content"
						@change="
							(val) => {
								tempNewContent = val
							}
						"
						editorClasses="w-full p-[12px] bg-gray-100 min-h-[180px] max-h-[500px] text-[16px]"
						class="rounded-[8px]"
					>
						<template #top-section="{ editor }">
							<div class="flex flex-col">
								<div
									class="block mb-2 text-sm leading-4 text-gray-700"
								>
									Article
								</div>
								<div
									class="flex flex-row items-center space-x-1.5 p-1.5 rounded-t-[8px] border bg-gray-50"
								>
									<div
										v-for="item in [
											'bold',
											'italic',
											'|',
											'quote',
											'code',
											'|',
											'numbered-list',
											'bullet-list',
											'left-align',
											'center-align',
											'right-align',
										]"
										:key="item"
									>
										<TextEditorMenuItem
											:item="item"
											:editor="editor"
										/>
									</div>
								</div>
							</div>
						</template>
					</CustomTextEditor>
					<ErrorMessage :message="articleInputErrors.content" />
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import CustomTextEditor from "@/components/global/CustomTextEditor.vue"
import TextEditorMenuItem from "@/components/global/TextEditorMenuItem.vue"
import { ErrorMessage } from "frappe-ui"
import { ref, inject } from "vue"

export default {
	name: "ArticleTitleAndContent",
	props: ["title", "content", "editable", "articleResource", "isNew"],
	components: {
		CustomTextEditor,
		TextEditorMenuItem,
		ErrorMessage,
	},
	mounted() {
		this.$event.on("save_current_article", (publish = false) => {
			this.save(publish)
		})

		this.saveArticleTitleAndContent = this.save
	},
	unmounted() {
		this.$event.off("save_current_article")
	},
	watch: {
		tempNewTitle(val) {
			this.updateNewArticleInput({ field: "title", value: val })
		},
		tempNewContent(val) {
			this.updateNewArticleInput({ field: "content", value: val })
		},
	},
	setup(props) {
		const tempNewTitle = ref(props.title)
		const tempNewContent = ref(props.content)

		const editMode = inject("editMode")
		const updateNewArticleInput = inject("updateNewArticleInput")
		const articleInputErrors = inject("articleInputErrors")

		const saveArticleTitleAndContent = inject("saveArticleTitleAndContent")

		return {
			tempNewTitle,
			tempNewContent,
			editMode,
			articleInputErrors,
			updateNewArticleInput,
			saveArticleTitleAndContent,
		}
	},
	methods: {
		save(publish = false) {
			this.articleResource.setValue.submit({
				title: this.tempNewTitle,
				content: this.tempNewContent,
				published: publish,
			})
			this.editMode = false
		},
	},
}
</script>
