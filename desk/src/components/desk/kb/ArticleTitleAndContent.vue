<template>
	<div>
		<div v-if="(editable && editMode) || isNew">
			<div class="flex flex-col space-y-[16px] h-full">
				<div>
					<Input
						label="Title"
						type="text"
						:value="article.title"
						@input="onTitleInput"
					/>
					<ErrorMessage :message="articleInputErrors.title" />
				</div>
				<div>
					<CustomTextEditor
						:show="true"
						ref="contentEditor"
						@click="$refs.contentEditor.focusEditor()"
						:content="article.content"
						@change="onContentInput"
						editorClasses="w-full px-2 bg-gray-100 h-[500px] text-[16px]"
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
		<div v-else class="flex flex-col space-y-[16px] h-full">
			<div class="font-semibold text-[24px]">
				{{ article.title }}
			</div>
			<TextEditor
				:editor-class="editable ? 'overflow-y-scroll' : ''"
				:editable="false"
				:content="article.content"
			/>
		</div>
	</div>
</template>

<script>
import CustomTextEditor from "@/components/global/CustomTextEditor.vue"
import TextEditorMenuItem from "@/components/global/TextEditorMenuItem.vue"
import { ErrorMessage, debounce, TextEditor } from "frappe-ui"
import { ref, inject } from "vue"

export default {
	name: "ArticleTitleAndContent",
	props: ["article", "editable", "editMode", "isNew"],
	components: {
		CustomTextEditor,
		TextEditorMenuItem,
		ErrorMessage,
		TextEditor,
	},
	setup() {
		const updateArticleTempValues = inject("updateArticleTempValues")
		const articleInputErrors = inject("articleInputErrors")

		return {
			articleInputErrors,
			updateArticleTempValues,
		}
	},
	resources: {
		checkIfTitleExists() {
			return {
				method: "frappedesk.api.kb.check_if_article_title_exists",
				onSuccess: (exists) => {
					if (exists) {
						this.articleInputErrors.title =
							"Article with this title already exists"
					} else {
						this.articleInputErrors.title = ""
					}
				},
			}
		},
	},
	methods: {
		onTitleInput: debounce(function (value) {
			this.$resources.checkIfTitleExists.submit({
				name: this.isNew ? "" : this.article.name,
				title: value,
			})
			this.updateArticleTempValues({ field: "title", value })
		}, 300),
		onContentInput: debounce(function (value) {
			this.updateArticleTempValues({ field: "content", value })
		}, 300),
	},
}
</script>
