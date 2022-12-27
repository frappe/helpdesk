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
				class="flex flex-row space-x-2 items-center"
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
						v-for="email in selectedOptions.slice().reverse()"
						class="flex items-center p-1 space-x-2 bg-white shadow rounded"
						:key="email"
						:title="email"
					>
						<span class="text-base ml-2">
							{{ email }}
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
			<!-- <div>
				<label class="block text-sm leading-4 text-gray-700"
					>Users</label
				>
				<VueMultiselect
					class="agentselect"
					v-model="selectedOptions"
					tag-placeholder="Add user"
					placeholder="Search user"
					label="user"
					:tag-position="top"
					:max-height="300"
					:color="grey"
					track-by="user"
					:tag-color="red"
					:options="options"
					:multiple="true"
					:taggable="true"
					@tag="addTag"
				></VueMultiselect>
				<pre class="language-json"><code>{{ value  }}</code></pre>
			</div> -->
		</div>
	</div>
</template>

<script>
import VueMultiselect from "vue-multiselect"
import Autocomplete from "@/components/global/Autocomplete.vue"
export default {
	name: "TeamTitleAndDescription",
	components: {
		VueMultiselect,
		Autocomplete,
	},
	props: ["name", "users", "editable", "ticketTypeResource"],
	data(props) {
		return {
			teamName: "",
			searchInput: "",
			selectedUser: "",
			selectedOptions: props.users,
			options: [],
		}
	},

	methods: {
		addTag(newTag) {
			const tag = {
				username: newTag,
				email:
					newTag.substring(0, 2) +
					Math.floor(Math.random() * 10000000),
			}
			this.selectedOptions.push(tag)
			this.options.push(tag)

			console.log(this.options, "options")
		},
		users() {
			this.$resources.getUser.fetch()
		},
		addUserToList(email) {
			this.selectedOptions = [
				...new Set([...this.selectedOptions, email]),
			]
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
		getUser() {
			return {
				method: "frappedesk.api.agent.get_agent_user",
				onSuccess: (res) => {
					this.options.length = 0
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

<style lang="css" src="vue-multiselect/dist/vue-multiselect.css">
.multiselect__tag {
	background: grey;
}

.multiselect__option--highlight {
	background: grey;
}

.multiselect__option--highlight:after {
	background: grey;
}

.multiselect__option--selected.multiselect__option--highlight {
	background: grey;
}

.multiselect__option--selected.multiselect__option--highlight:after {
	background: #798b91;
}

.multiselect__tag-icon:hover {
	background: grey;
}

.multiselect__input,
.multiselect__single {
	padding: 0 0 0 0;
}

.multiselect__placeholder {
	margin-left: 4px;
	color: #999999;
}
</style>
