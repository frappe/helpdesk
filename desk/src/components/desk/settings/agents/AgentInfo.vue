<template>
	<div class="min-w-[490px] px-[24px] py-[10px]">
		<div class="form w-full flex flex-col">
			<div class="float-left mb-[16px]" @click="() => {
				editingName = true
				tempAgentName = values.agentName
			}">
				<div v-if="!editingName" class="flex space-x-2 items-center cursor-pointer">
					<div class="font-semibold">{{ values.agentName }}</div>
					<FeatherIcon class="w-3 h-3" name="edit-2" />
				</div>
				<div v-else class="flex space-x-2 items-center">
					<Input id="agentNameInput" v-model="tempAgentName" type="text"/>
					<FeatherIcon class="w-4 h-4" role="button" name="x" @click="() => {
						editingName = false
						tempAgentName = values.agentName
					}" />
				</div>
			</div>
			<div class="flex flex-col space-y-[24px]">
				<div>
					<span class="block mb-2 text-sm leading-4 text-gray-700">Profile Picture</span>
					<div class="flex flex-row space-x-[8px] items-center">
						<CustomAvatar :label="values?.agentName" size="2xl" :imageURL="values?.profilePicture" />
						<div class="flex flex-row space-x-[8px]">
							<Button>Upload new</Button>
							<Button>Remove</Button>
						</div>
					</div>
				</div>
				<div class="flex flex-row space-x-[16px]">
					<div class="grow">
						<Input label="E-mail" type="text" :value="values?.email" @change="(val) => values.email = val"/>
					</div>
					<div class="grow">
						<Input label="Team" type="select" :options="teams" :value="values?.team" @change="(val) => values.team = val"/>
					</div>
				</div>
				<div class="grow">
					<Input label="Signature" type="textarea" :value="values?.signature" @change="(val) => values.signature = val"/>
				</div>
				<div class="w-full flex flex-row">
					<div>
						<Button @click="cancel()">Cancel</Button>
					</div>
					<div class="grow flex flex-row-reverse">
						<Button appearance="primary" @click="save()">Save</Button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ref } from 'vue'
import { FeatherIcon, Input } from 'frappe-ui'
import CustomAvatar from '@/components/global/CustomAvatar.vue'

export default {
	name: 'AgentInfo',
	props: ['agent'],
	components: {
		FeatherIcon,
		Input,
		CustomAvatar
	},
	setup() {
		const editingName = ref(false)
		const tempAgentName = ref('')

		return {
			editingName,
			tempAgentName
		}
	},
	computed: {
		agentDoc() {
			return this.$resources.agent.doc || null
		},
		userDoc() {
			return this.$resources.user.doc || null
		},
		values() {
			return {
				agentName: this.agentDoc?.agent_name || null,
				profilePicture: this.userDoc?.user_image || null,
				team: this.agentDoc?.group || null,
				email: this.userDoc?.email || null,
				signature: this.userDoc?.email_signature || null,
			}
		},
		teams() {
			if (this.$resources.teams.data) {
				return this.$resources.teams.data.map(team => {
					return team.name
				})
			} else {
				return []
			}
		}
	},
	deactivated() {
		this.resetForm()
	},
	resources: {
		agent() {
			return {
				type: 'document',
				doctype: 'Agent',
				name: this.agent
			}
		},
		user() {
			return {
				type: 'document',
				doctype: 'User',
				name: this.agent,
				setValue: {
					onSuccess: () => {
						this.$resources.agent.setValue.submit({
							agent_name: this.tempAgentName,
							group: this.values.team,
						})
						this.resetForm()
					}
				}
			}
		},
		teams() {
			return {
				type: 'list',
				doctype: 'Agent Group',
				fields: ['name']
			}
		}
	},
	methods: {
		resetForm() {
			this.editingName = false
			this.tempAgentName = this.values.agentName
		},
		save() {
			this.$resources.user.setValue.submit({
				email: this.values.email,
				email_signature: this.values.signature,
				full_name: this.tempAgentName,
			})
		},
		cancel() {
			this.resetForm()
		}
	}
}
</script>

<style>

</style>