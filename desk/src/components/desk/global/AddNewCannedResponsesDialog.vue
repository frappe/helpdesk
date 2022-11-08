<template>
	<div>
		<Dialog
			:options="{ title: 'New canned response', size: '3xl'}"
			:show="show"
			@close="close()"
		>
			<template #body-content>
				<div class="flex flex-col">

						<Input
							id="searchInput"
							class="w-full"
							type="text"
							label="Title"
							placeholder="Enter Title"
							v-model="title"
							/>
							<ErrorMessage :message="titleValidationError" />

				</div>
				<div
					class="mb-2 block text-sm leading-4 text-gray-700"
				>
					Message
				</div>
				<div>
					<TextEditor
						class="bg-gray-100"
						ref="textEditor"
						editor-class="min-h-[20rem] overflow-y-auto max-h-[73vh] w-full px-3"
						:content="message"
						:starterkit-options="{
						heading: { levels: [2, 3, 4, 5, 6] },
						}"
						@change="(val)=>{
							message=val
						}"
					>

					<template v-slot:top>
						<div>
							<TextEditorFixedMenu
								class="m-3 overflow-x-auto"
								:buttons="textEditorMenuButtons"
							/>
						</div>
					</template>


					</TextEditor>
					<!-- <CustomTextEditor
						:show="true"
						:content="message"						
						@change="(val)=>{
							message=val
						}"
						editorClasses="w-full p-[7px]  bg-gray-100 min-h-[180px] max-h-[500px] text-[12px] max-w-full"
						class="rounded-[8px]"
					>
					<template #top-section="{ editor }">
						<div class="flex flex-col">
							<div
							class="block mb-2 text-sm leading-4 text-gray-700"
							>
							Message
							</div>
							<div class="flex flex-row items-center space-x-1.5 p-1.5 rounded-t-[8px] border bg-gray-50">
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
					</CustomTextEditor> -->
					
				</div>
				<ErrorMessage :message="messageValidationError" />
			</template>
			<template #actions>
				<Button
					appearance="primary"
					@click="addResponse()"
                    class="mr-auto"
					>Add Response</Button
				>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Dialog, Input, FeatherIcon, ErrorMessage, TextEditor } from "frappe-ui"
import { ref } from "@vue/reactivity"
// import CustomTextEditor from "@/components/global/CustomTextEditor.vue"
// import TextEditorMenuItem from "@/components/global/TextEditorMenuItem.vue"
import { TextEditorFixedMenu } from "frappe-ui/src/components/TextEditor"
export default {
	name: "AddNewCannedResponsesDialog",
	props: ["show"],
	components: {
		Dialog,
		Input,
		FeatherIcon,
		ErrorMessage,
		TextEditor,
		TextEditorFixedMenu
	},
	setup() {

		const titleValidationError=ref("")
		const messageValidationError=ref("")
		return {
			titleValidationError,
			messageValidationError
		}
	},

	data(){
		return{
			title:"",
			message:""
		}

	},

	watch:{
		title(newValue){
			this.validateTitle(newValue)
		},
		message(newValue){
			this.validateMessage(newValue)
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
		close() {
			this.title = ""
			this.message = ""
			this.$emit("close")
		},
		addResponse(){
			if (this.validateInputs()) {
				return
			}
			const inputParams={
				title:this.title,
				message:this.message
			}
			this.$resources.newResponse.submit({
				doc:{
					doctype:"Canned Response",
					...inputParams,
				}
			})
		},
		validateInputs(){
			let error = this.validateTitle(this.title)
			error += this.validateMessage(this.message)

			return error
		},
		validateTitle(value){
			this.titleValidationError = ""
			if(!value){
				this.titleValidationError="Title is required"
			}
			else if(value.trim() == ""){
				this.titleValidationError = "Title is required"
			}

			return this.titleValidationError

		},

		validateMessage(value){
			this.messageValidationError = ""
			if(!value){
				this.messageValidationError = "Message is required"
			}
			else if(
				["<p><br></p>", "<p></p>"].includes(value.replaceAll(" ", ""))
			){
				this.messageValidationError = "Message is required"
			}

			return this.messageValidationError
		}
	},
	resources: {
		newResponse(){
			return {
				method:"frappe.client.insert",
				onSuccess: (doc)=>{
					this.$router.push(
						`/frappedesk/settings/canned_responses/${doc.name}`
					)
				},
				onError: (err)=>{
					this.$toast({
						title: "Error while creating canned response",
						text: err,
						customIcon: "circle-fail",
						appearance: "danger",
					})
				}
			}
		}
	},
}
</script>