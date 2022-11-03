<template>
	<div>
		<Dialog
			:options="{ title: 'New canned response' }"
			:show="show"
			@close="close()"
		>
			<template #body-content>
				<div class="space-y-6">
					<form
						@submit.prevent="onSubmit"
						class="flex flex-row space-x-5 items-center"
					>
						<Input
							id="searchInput"
							class="w-full"
							type="text"
							placeholder="Enter Title"
							@input="(val) => {
								tempNewTitle=val
							}"
						/>
					</form>
				</div>
				<div>
					<CustomTextEditor

						:show="true"
						ref="contentEditor"
						@click="$refs.contentEditor.focusEditor()"
						@change="(res)=>{
							tempNewMessage=res
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
			</template>
			<template #actions>
				<Button
					appearance="primary"
					@click="addResponse()"
					>Add Response</Button
				>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Dialog, Input, FeatherIcon } from "frappe-ui"
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
		CustomTextEditor,
		TextEditorMenuItem
	},
	setup() {
		const tempNewTitle=ref("")
		const tempNewMessage=ref("")
		const responseInputErrors=ref("")
		return {
			tempNewMessage,
			tempNewTitle,
			responseInputErrors
		}
	},
	methods: {
		close() {
			this.tempNewTitle = ""
			this.tempNewMessage = ""
			this.$emit("close")
		},
		addResponse(){
			const inputParams={
				title:this.tempNewTitle,
				message:this.tempNewMessage
			}
			this.$resources.newResponse.submit({
				doc:{
					doctype:"Canned Response",
					...inputParams,
				}
			})
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