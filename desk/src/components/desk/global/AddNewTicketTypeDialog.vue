<template>
	<div>
		<Dialog
			:options="{ title: 'Add New Ticket Type', size: '2xl' }"
			v-model="open"
		>
			<template #body-content>
				<div class="space-y-4">
					<div class="space-y-1">
						<Input
							label="Ticket Type Name"
							type="text"
							placeholder="Incident"
							v-model="ticketTypeName"
						/>
					</div>
					<div class="w-full space-y-1">
						<div>
							<span class="block text-sm leading-4 text-gray-700">
								Priority
							</span>
						</div>
						<Autocomplete
							:value="selectedPriority"
							@change="
								(item) => {
									if (!item) {
										return
									}
									selectedPriority = item.value
								}
							"
							:resourceOptions="{
								url: 'helpdesk.extends.client.get_list',
								inputMap: (query) => {
									return {
										doctype: 'HD Ticket Priority',
										pluck: 'name',
										filters: [
											['name', 'like', `%${query}%`],
										],
									}
								},
								responseMap: (res) => {
									return res.map((d) => {
										return {
											label: d.name,
											value: d.name,
										}
									})
								},
							}"
						/>
					</div>
					<div class="block text-sm leading-4 text-gray-700">
						Description
					</div>

					<div class="relative px-3 py-2 mt-2 border rounded-md">
						<TextEditor
							editor-class="min-h-[4rem] prose-sm"
							:content="description"
							placeholder="Description"
							@change="(val) => (description = val)"
							:bubbleMenu="true"
						/>
					</div>

					<div class="flex float-right space-x-2">
						<Button
							appearance="primary"
							@click="
								() => {
									addTicketType()
									close()
									this.$router.go()
								}
							"
							class="mr-auto"
							>Add</Button
						>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Input, Dialog, TextEditor } from "frappe-ui"
import { computed, ref } from "vue"
import Autocomplete from "@/components/global/Autocomplete.vue"
export default {
	name: "AddNewTicketDialog",
	props: {
		modelValue: {
			type: Boolean,
			required: true,
		},
	},
	setup(props, { emit }) {
		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit("update:modelValue", val)
				if (!val) {
					emit("close")
				}
			},
		})

		let selectedPriority = ref("")
		return {
			open,
			selectedPriority,
		}
	},
	components: {
		Dialog,
		Input,
		TextEditor,
		Autocomplete,
	},
	data() {
		return {
			ticketTypeName: "",
			description: "",
			Autocomplete,
		}
	},
	methods: {
		addTicketType() {
			const inputParams = {
				name: this.ticketTypeName,
				priority: this.selectedPriority,
				description: this.description,
			}
			this.$resources.newTicketType.submit({
				doc: {
					doctype: "HD Ticket Type",
					...inputParams,
				},
			})
		},
		close() {
			this.ticketTypeName = ""
			this.$emit("close")
		},
	},
	resources: {
		newTicketType() {
			return {
				url: "frappe.client.insert",
				onSuccess: (doc) => {
					this.$router.push(`/ticket-types`)
				},
			}
		},
	},
}
</script>
