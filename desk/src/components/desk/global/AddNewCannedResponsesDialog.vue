<template>
	<div>
		<Dialog
			:options="{ title: 'New canned response', size: '3xl'}"
			:show="show"
			@close="close()"
		>
			<template #body-content>
				<div class="space-y-6">
					
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
				<div>
					<CustomTextEditor
						:show="true"
						:content="message"
						@change="(val)=>{
							message=val
						}"
						editorClasses="w-full p-[12px] bg-gray-100 min-h-[180px] max-h-[500px] text-[16px]"
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
					</CustomTextEditor>
					
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
import { Dialog, Input, FeatherIcon, ErrorMessage } from "frappe-ui"
import { ref } from "@vue/reactivity"
import CustomTextEditor from "@/components/global/CustomTextEditor.vue"
import TextEditorMenuItem from "@/components/global/TextEditorMenuItem.vue"
export default {
	name: "AddNewCannedResponsesDialog",
	props: ["show"],
	components: {
		Dialog,
		Input,
		FeatherIcon,
		ErrorMessage,
		CustomTextEditor,
		TextEditorMenuItem
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