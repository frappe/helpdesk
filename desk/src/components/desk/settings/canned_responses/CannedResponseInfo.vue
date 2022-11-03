<template>
	<div class="min-w-[490px] px-[24px] py-[10px]">
		<div class="shrink-0 h-[72px] py-[22px] flow-root px-[16px]">
			<div class="float-left">
				<router-link
					:to="`/frappedesk/settings/canned_response`"
					class="my-1 text-[12px] text-gray-600 stroke-gray-600 flex flex-row items-center space-x-1 hover:text-gray-700 hover:stroke-gray-700 select-none"
					role="button"
				>
				<FeatherIcon name="arrow-left" class="w-[13px] h-[13px]" />
				<div>
					Back to response list
				</div>
				</router-link>

			</div>
			<div class="float-right">
				<div v-if="!editMode" class="flex flex-row space-x-2">
					<Button
					appearance="secondary"
					@click="()=>{
						editMode = true
						newAResponseTempValues={
							title: cannedResponseDoc.title,
							message:cannedResponseDoc.message
						}
					}"					
					>Edit</Button>
				</div>
				<div v-else class="flex flex-row space-x-2">
					<Button
					appearance="secondary"
					@click="()=>{
						this.$router.go()
					}"
					>
					Cancel
					</Button>
					<Button 
					appearance="primary" @click="saveResponse()"
					>
					Save
					</Button>
				</div>
			</div>
		</div>
		<div class="flex flex-row space-x-[24px] h-full border-t px-[16px] py-[22px]">

			<ResponseTitleAndMessage
				class="grow"
				:title="values?.cannedResponseName"
				:message="values?.message"
				:editable="editMode"
				:responseResource="$resources.cannedResponse"
			/>
		</div>
	</div>
</template>
<script>
import { ref,provide } from "vue"
import { FeatherIcon, Input } from "frappe-ui"
import ResponseTitleAndMessage from "@/components/desk/settings/canned_responses/ResponseTitleAndMessage.vue"

export default {
	name: "CannedResponseInfo",
	props: ["canned_response"],
	components: {
		FeatherIcon,
		Input,
		ResponseTitleAndMessage
	},
	setup(props) {
		const editingName = ref(false)
		const newResponseTempValues = ref({})
		const updateNewResponseInput = ref((input)=>{
			newResponseTempValues.value[input.field] = input.value
		})
		provide("updateNewResponseInput", updateNewResponseInput)
		provide("newResponseTempValues", newResponseTempValues)
		const saveResponseTitleAndMessage=ref(()=>{})
		provide("saveResponseTitleAndMessage", saveResponseTitleAndMessage)
		const tempCannedResponseName = ref("")
		const updatingValues = ref(false)
		const editMode=ref(!props.canned_response)
		provide("editMode", editMode)
	
		
		return {
			editingName,
			tempCannedResponseName,
			updatingValues,
			editMode,
			newResponseTempValues,
			saveResponseTitleAndMessage
		}
	},
	computed: {
		cannedResponseDoc() {
			return this.$resources.cannedResponse.doc || null
		},
		values() {
			if (this.updatingValues) {
				return this.values || null
			}
			return {
				cannedResponseName: this.cannedResponseDoc?.title || null,
				message: this.cannedResponseDoc?.message || null
			}
		},
	},
	deactivated() {
		this.resetForm()
	},
	resources: {
		cannedResponse() {
			return {
				type: "document",
				doctype: "Canned Response",
				name: this.canned_response,
				setValue: {
					onSuccess: () => {
						this.$toast({
							title: "Canned Response Updated.",
							customIcon: "circle-check",
							appearance: "success",
						})
					},
					onError:(err)=>{
						this.$toast({
							title: "Error while updating canned response",
							text: err,
							customIcon: "circle-fail",
							appearance: "danger",
						})
					}
				},
			}
		},
	},
	methods: {
		resetForm() {
			this.editingName = false
			this.tempCannedResponseName = this.values.cannedResponseName
		},
		save() {
			this.updatingValues = true
			const newValues = this.values
			this.$resources.user.setValue
				.submit({
					title: newValues.title,
					message: newValues.message,
				})
				.then(() => {
					this.$resources.cannedResponse.setValue.submit({
						title: this.tempCannedResponseName,
					})
				})
		},
		saveResponse(){
			const inputParams={
				title:this.newResponseTempValues.title,
				message:this.newResponseTempValues.message
			}
			this.$resources.cannedResponse.setValue.submit({
				...inputParams
			})
			this.editMode = false
		},
		cancel() {
			this.$router.go()
		},
	},
}
</script>
