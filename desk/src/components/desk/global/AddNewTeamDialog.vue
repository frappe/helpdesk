<template>
	<div>
		<Dialog :options="{ title: 'Add New Team', size: 'sm' }" v-model="open">
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
					<div>
						<label class="block text-sm leading-4 text-gray-700"
							>Users</label
						>
						<VueMultiselect
							class="agentselect"
							v-model="selectedOptions"
							tag-placeholder="Add user"
							placeholder="Search user"
							label="email"
							:tag-position="top"
							track-by="email"
							:tag-color="red"
							:options="options"
							:multiple="true"
							:taggable="true"
							@tag="addTag"
						></VueMultiselect>
						<pre
							class="language-json"
						><code>{{ value  }}</code></pre>
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
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { Input, Dialog } from "frappe-ui"
import { computed, ref } from "vue"
import VueMultiselect from "vue-multiselect"

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

		return {
			open,
		}
	},
	components: {
		Dialog,
		Input,
		VueMultiselect,
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
				users: this.options,
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
			this.$emit("close")
		},
		addTag(newTag) {
			const tag = {
				username: newTag,
				email:
					newTag.substring(0, 2) +
					Math.floor(Math.random() * 10000000),
			}
			this.selectedOptions.push(tag)
			this.options.push(tag)
		},
		users() {
			this.$resources.getUser.fetch()
		},
	},
	resources: {
		newTeam() {
			return {
				method: "frappe.client.insert",
				onSuccess: (doc) => {
					this.$router.push(`/frappedesk/teams`)
				},
			}
		},
		getUser() {
			return {
				method: "frappedesk.api.agent.get_agent_user",
				onSuccess: (res) => {
					this.options.length = 0
					res.map((value) => {
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
.agentselect .multiselect__tags {
	background-color: black;
}
</style>
