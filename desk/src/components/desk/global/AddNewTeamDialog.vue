<template>
	<div>
		<Dialog
			:options="{ title: 'Add New Team', size: '3xl' }"
			v-model="open"
		>
			<template #body-content>
				<div class="space-y-4">
					<div class="space-y-1">
						<Input
							label="Team Name"
							type="text"
							placeholder="Product Expert"
							v-model="teamName"
						/>
					</div>
					<form
						@submit.prevent="onSubmit"
						class="flex flex-row space-x-2 items-end"
					>
						<div class="w-full space-y-1">
							<div>
								<span
									class="block text-sm leading-4 text-gray-700"
								>
									Users
								</span>
							</div>
							<Autocomplete
								id="searchInput"
								:value="selectedUser"
								@change="
									(item) => {
										if (!item) {
											return
										}
										selectedUser = item.value
									}
								"
								:resourceOptions="{
									method: 'frappe.client.get_list',
									inputMap: (query) => {
										return {
											doctype: 'User',
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
						<Button
							v-if="selectedUser != ''"
							appearance="primary"
							type="submit"
							icon="arrow-down"
							@click="
								() => {
									addUserToList(selectedUser)
									clearSearchInput()
								}
							"
						>
							Add
						</Button>
					</form>
					<div
						class="bg-gray-100 min-h-[100px] max-h-[300px] overflow-y-scroll px-2 rounded border flex flex-col"
					>
						<ul
							v-if="selectedOptions.length"
							class="flex flex-wrap gap-2 py-2"
						>
							<li
								v-for="email in selectedOptions
									.slice()
									.reverse()"
								class="flex items-center p-1 space-x-2 bg-white shadow rounded"
								:key="email.user"
							>
								<span class="text-base ml-2">
									{{ email.user }}
								</span>
								<button
									class="grid w-4 h-4 text-gray-700 rounded hover:bg-gray-300 place-items-center"
									@click="removeUserFromList(email)"
								>
									<FeatherIcon class="w-3" name="x" />
								</button>
							</li>
						</ul>
					</div>

					<div class="flex float-right space-x-2">
						<Button
							appearance="primary"
							@click="
								() => {
									addTeam()
									close()
									this.$router.go()
								}
							"
							class="mr-auto"
							>Add</Button
						>
					</div>
					<div class="flex flex-row gap-2">
						<Button appearance="secondary" @click="close()"
							>Cancel</Button
						>

						<Button @click="removeAllUserFromList()">
							Clear All
						</Button>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Input, Dialog, FeatherIcon } from "frappe-ui"
import { computed, ref } from "vue"
import Autocomplete from "@/components/global/Autocomplete.vue"

export default {
	name: "AddNewTeamDialog",
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
		let selectedUser = ref("")
		const searchInput = ref("")

		return {
			open,
			selectedUser,
			searchInput,
		}
	},
	components: {
		Dialog,
		Input,
		Autocomplete,
		FeatherIcon,
	},
	data() {
		return {
			teamName: "",
			selectedOptions: [],
			options: [],
		}
	},
	methods: {
		addTeam() {
			const inputParams = {
				team_name: this.teamName,
				users: this.selectedOptions,
			}
			this.$resources.newTeam.submit({
				doc: {
					doctype: "Agent Group",
					...inputParams,
				},
			})
		},
		close() {
			this.teamName = ""
			this.selectedOptions = []
			this.searchInput = ""
			this.$emit("close")
		},
		addUserToList(email) {
			let user = {}
			user["user"] = email
			this.selectedOptions = [...new Set([...this.selectedOptions, user])]
		},
		removeAllUserFromList() {
			this.selectedOptions = []
		},
		removeUserFromList(email) {
			this.selectedOptions = this.selectedOptions.filter(
				(item) => item !== email
			)
		},
		clearSearchInput() {
			this.searchInput = ""

			this.selectedUser = ""
		},
	},
	resources: {
		newTeam() {
			return {
				method: "frappe.client.insert",
				onSuccess: (doc) => {
					console.log(doc, "document")
					this.$router.push(`/frappedesk/teams`)
				},
			}
		},
	},
}
</script>
