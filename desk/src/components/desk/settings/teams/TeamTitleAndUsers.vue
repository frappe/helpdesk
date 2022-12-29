<template>
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
			<form
				@submit.prevent="onSubmit"
				class="flex flex-row space-x-2 items-end"
			>
				<div class="w-full space-y-1">
					<div>
						<span class="block text-sm leading-4 text-gray-700">
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
									fields: ['name', 'username', 'email'],
									filters: {
										name: ['like', `%${query}%`],
									},
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
						v-for="email in selectedOptions"
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
		</div>
	</div>
</template>

<script>
import Autocomplete from "@/components/global/Autocomplete.vue"
import { Input, FeatherIcon } from "frappe-ui"
import { ref, inject } from "vue"
export default {
	name: "TeamTitleAndUsers",
	components: {
		Autocomplete,
		FeatherIcon,
	},

	props: ["name", "users", "editable", "teamResource"],
	mounted() {
		this.saveTeamTitleAndUsers = this.save
	},
	watch: {
		teamName(val) {
			this.updateNewTeamInput({ field: "team_name", value: val })
		},
		selectedOptions(val) {
			this.updateNewTeamInput({
				field: "users",
				value: this.selectedOptions,
			})
		},
	},
	setup(props) {
		const teamName = ref(props.name)
		const searchInput = ref("")
		const selectedUser = ref("")
		const updateNewTeamInput = inject("updateNewTeamInput")
		const saveTeamTitleAndUsers = inject("saveTeamTitleAndUsers")
		const selectedOptions = ref(props.users)
		const options = ref([])
		return {
			teamName,
			searchInput,
			selectedUser,
			updateNewTeamInput,
			saveTeamTitleAndUsers,
			selectedOptions,
			options,
		}
	},

	methods: {
		save() {
			this.teamResource.setValue.submit({
				team_name: this.teamName,
				users: this.selectedOptions,
			})
		},
		users() {
			this.$resources.getUser.fetch()
		},
		addUserToList(email) {
			let user = {}
			user["user"] = email
			this.selectedOptions = [...new Set([...this.selectedOptions, user])]
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
		getUser() {
			return {
				method: "frappedesk.api.agent.get_agent_user",
				onSuccess: (res) => {
					res.map((value) => {
						value["user"] = value["email"]
						delete value["username"]
						delete value["email"]
						this.options.push(value)
					})
				},
				auto: true,
			}
		},
	},
}
</script>
