<template>
	<div class="flex flex-col w-full border-r pt-[23px]" :style="{ height: viewportWidth > 768 ? 'calc(100vh)' : null }">
		<div class="mb-[38.4px] pl-[22px]">
			<CustomIcons name="frappedesk" class="w-[67.84px] h-[16.6px]"/>
		</div>
		<div class="mb-auto space-y-[6px] text-base select-none">
			<div v-for="option in options" :key="option.label">
				<div 
					class="group stroke-gray-600 stroke-1 cursor-pointer hover:bg-gray-200 hover:text-gray-800" 
					:class="
						option.selected ? 
						'bg-gray-200 text-gray-800 font-medium' : 
						(
							option.children && option.children.find(element => element.selected) ? 
							'font-medium text-gray-800' : 
							'font-normal text-gray-600'
						)
						"
					@click="() => {
						option.action ? option.action() : ( option.children ? option.expanded = !option.expanded : {} )  
					}"
				>
					<div class="pl-[22px] h-[30px] flex items-center space-x-[8px]">
						<CustomIcons :name="option.icon" class=" h-[14px] w-[14px]"/>
						<span class="grow">{{ option.label }}</span>
						<div v-if="option.children" class="pr-[17.81px]">
							<CustomIcons class="h-[6px] fill-gray-400" :name="option.expanded ? 'chevron-up' : 'chevron-down'" />
						</div>
					</div>
				</div>
				<div v-if="option.children && option.expanded">
					<div>
						<div v-for="childOption in option.children" :key="childOption.label">
							<div 
								class="group h-[30px] flex items-center cursor-pointer hover:bg-gray-200 hover:text-gray-800"
								:class="childOption.selected ? 'bg-gray-200 text-gray-800 font-medium' : 'font-normal text-gray-600 '"
								@click="() => { childOption.action ? childOption.action() : {} }"
							>
								<div class="pl-[46px]">
									<span>
										{{ childOption.label }}
									</span>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div>
			<div class="flex items-center text-base pl-[15px] pb-[22px] space-x-[7px] text-gray-700 font-normal cursor-pointer">
				<div>
					<CustomAvatar :label="user.username" class="cursor-pointer" size="lg" v-if="user" :imageURL="user.profile_image" />
				</div>
				<span class="truncate">{{ user.agent ? user.agent.agent_name : user.user }}</span>
			</div>
		</div>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { Dropdown } from 'frappe-ui'
import CustomAvatar from "@/components/global/CustomAvatar.vue"
import { inject, ref } from 'vue'

export default {
	name: 'SideBarMenu',
	components: {
		CustomIcons,
		Dropdown,
		CustomAvatar
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		
		const user = inject('user')

		const ticketFilter = inject('ticketFilter')

		const iconHeight = ref(30)
		const iconWidth = ref(30)

		const options = ref()

		return { viewportWidth, user, ticketFilter, iconHeight, iconWidth, options }
	},
	mounted() {
		this.options = [
			{
				label: 'Ticketing',
				icon: 'ticket',
				expanded: true,
				children: [
					{
						label: 'All Tickets',
						action: () => {
							this.$router.push({path: '/frappedesk/tickets'})
							this.ticketFilter = 'All Tickets'
						}
					},	// TODO: only add assigned and unassigend tickets if the user is a agent
				]
			},
			{
				label: 'Knowledge Base',
				icon: 'knowledge-base',
				action: () => {
					this.select('Knowledge Base')
					this.$router.push({path: '/frappedesk/knowledge-base'})
				}
			},
			{
				label: 'Reports',
				icon: 'reports',
				action: () => {
					this.select('Reports')
					this.$router.push({path: '/frappedesk/reports'})
				}
			},
			{
				label: 'Contacts',
				icon: 'customers',
				children: [
					{
						label: 'Contacts',
						action: () => {
							this.select('Contacts')
							this.$router.push({path: '/frappedesk/contacts'})
						}
					},
					{
						label: 'Organisations',
						action: () => {
							this.select('Organisations')
							// this.$router.push({path: '/frappedesk/organisations'})
						}
					}
				]
			},
			{
				label: 'Settings',
				icon: 'settings',
				action: () => {
					this.select('Settings')
					this.$router.push({path: '/frappedesk/settings'})
				}
			}
		]

		if (this.user.agent) {
			this.options.find(option => option.label == 'Ticketing').children.push(...[
				{
					label: 'Assigned Tickets',
					action: () => {
						this.$router.push({path: '/frappedesk/tickets'})
						this.ticketFilter = 'Assigned Tickets'
					}
				},
				{
					label: 'Unassigned Tickets',
					action: () => {
						this.select('Unassigned Tickets')
						this.$router.push({path: '/frappedesk/tickets'})
						this.ticketFilter = 'Unassigned Tickets'
					}
				}
			])
		}

		// When the page is refreshed / opened the selected side bar option will  be set 
		if (this.$route.path.includes('frappedesk/tickets')) {
			this.select('All Tickets')
		} else if (this.$route.path.includes('frappedesk/knowledge-base')) {
			this.select('Knowledge Base')
		} else if (this.$route.path.includes('frappedesk/reports')) {
			this.select('Reports')
		} else if (this.$route.path.includes('frappedesk/contacts')) {
			this.select('Contacts')
		} else if (this.$route.path.includes('frappedesk/settings')) {
			this.select('Settings')
		}
	},
	watch: {
		ticketFilter(newValue) {
			this.select(newValue)
		}
	},
	methods: {
		select(label) {
			this.options.forEach(option => {
				if (option.children) {
					option.children.forEach(childOption => {
						childOption.selected = (childOption.label == label)
					})
				}
				if (option.label == label) {
					if (!option.children) {
						option.selected = true
					} else {
						option.selected = false
					}
				} else {
					option.selected = false
				}
			});
		},
		avatarOptions() {
			let items = [];
			["Log out"].forEach(item => {
				items.push({
				label: item,
					handler: () => {
						this.user.logout()
					},
				});
			});
			return items;
		},
	}
}

</script>