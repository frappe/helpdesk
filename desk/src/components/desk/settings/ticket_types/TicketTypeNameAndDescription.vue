<template>
	<div>
		<div>
			<div class="flex flex-col space-y-[16px] h-full">
				<div>
					<Input
						label="Title"
						type="text"
						:value="name"
						@input="
							(val) => {
								tempNewName = val
							}
						"
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
							method: 'frappe.client.get_list',
							inputMap: (query) => {
								return {
									doctype: 'Ticket Priority',
									pluck: 'name',
									filters: [['name', 'like', `%${query}%`]],
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
				<div class="flex flex-col">
					<div class="mb-2 block text-sm leading-4 text-gray-700">
						Description
					</div>
					<TextEditor
						:class="'bg-gray-100'"
						ref="textEditor"
						:editor-class="'min-h-[20rem] overflow-y-auto max-h-[73vh] px-3 max-w-full'"
						:content="description"
						:starterkit-options="{
							heading: { levels: [2, 3, 4, 5, 6] },
						}"
						@change="
							(val) => {
								tempNewDescription = val
							}
						"
					>
					</TextEditor>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { TextEditor } from "frappe-ui"
import { ref, inject } from "vue"
import Autocomplete from "@/components/global/Autocomplete.vue"
export default {
	name: "TicketTypeNameAndDescription",
	props: [
		"name",
		"description",
		"editable",
		"priority",
		"ticketTypeResource",
	],
	components: {
		TextEditor,
		Autocomplete,
	},
	mounted() {
		this.saveTicketTypeNameAndDescription = this.save
	},
	watch: {
		tempNewName(val) {
			this.updateNewTicketTypeInput({ field: "name", value: val })
		},
		tempNewDescription(val) {
			this.updateNewTicketTypeInput({ field: "description", value: val })
		},
		selectedPriority(val) {
			this.updateNewTicketTypeInput({ field: "priority", value: val })
		},
	},
	setup(props) {
		const tempNewName = ref(props.name)
		const tempNewDescription = ref(props.description)
		const editMode = inject("editMode")
		const updateNewTicketTypeInput = inject("updateNewTicketTypeInput")
		const saveTicketTypeNameAndDescription = inject(
			"saveTicketTypeNameAndDescription"
		)
		const selectedPriority = ref(props.priority)
		return {
			tempNewName,
			tempNewDescription,
			editMode,
			updateNewTicketTypeInput,
			saveTicketTypeNameAndDescription,
			selectedPriority,
		}
	},
	methods: {
		save() {
			this.ticketTypeResource.setValue.submit({
				name: this.tempNewName,
				description: this.tempNewDescription,
				priority: this.selectedPriority,
			})
			this.editMode = false
		},
	},
}
</script>
