<template>
	<div class="flex flex-col w-full border-r pt-[23px]" :style="{ height: viewportWidth > 768 ? 'calc(100vh)' : null }">
		<div class="mb-[38.4px] pl-[22px] cursor-pointer">
			<CustomIcons name="frappedesk" class="w-[67.84px] h-[16.6px]" @click="() => {$router.push({path: '/frappedesk/tickets'})}"/>
		</div>
		<div class="mb-auto space-y-[6px] text-base select-none">
			<div v-for="option in menuOptions" :key="option.label">
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
			<div class="mx-[8px] mb-[17px] flex flex-col">
				<div v-if="showProfileSettings" class="rounded-[6px] bg-white h-50 shadow-md z-50 px-[7px] py-[6px]">
					<div v-for="item in profileSettings" :key="item.label">
						<div 
							class="flex flex-row items-center text-base font-normal hover:bg-gray-100 cursor-pointer px-[13px] py-[5px] rounded-[8px] space-x-[10px]" 
							:class="item.style"
							@click="item.action()"
						>
							<CustomIcons class="h-[16px] w-[16px]" :name="item.icon" />
							<span>{{ item.label }}</span>
						</div>
					</div>
				</div>
				<div
					@click="() => { showProfileSettings = !showProfileSettings }" 
					v-on-outside-click="() => { showProfileSettings = false }"
					class="flex flex-row items-center px-[14px] space-x-[7px] cursor-pointer hover:bg-gray-100 py-[12px] rounded-[6px]" 
					:class="showProfileSettings ? 'bg-gray-100' : ''"
				>
					<div>
						<CustomAvatar :label="user.username" class="cursor-pointer" size="lg" v-if="user" :imageURL="user.profile_image" />
					</div>
					<div class="flex flex-col text-gray-700">
						<span class="truncate text-base font-medium">{{ user.agent ? user.agent.agent_name : user.user }}</span>
						<span class="truncate text-[11px] font-normal">{{ user.user }}</span>
					</div>
				</div>
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

		const menuOptions = ref()
		const profileSettings = ref()
		const showProfileSettings = ref(false)

		return { viewportWidth, user, ticketFilter, iconHeight, iconWidth, menuOptions, profileSettings, showProfileSettings }
	},
	mounted() {
		this.menuOptions = [
			{
				label: 'Ticketing',
				icon: 'ticket',
				expanded: true,
				children: [
					{
						label: 'All Tickets',
						action: () => {
							this.select('All Tickets')
							this.ticketFilter = 'All Tickets'
							this.$router.push({path: '/frappedesk/tickets'})
						}
					},	// TODO: only add assigned and unassigend tickets if the user is a agent
				]
			},
			// {
			// 	label: 'Knowledge Base',
			// 	icon: 'knowledge-base',
			// 	action: () => {
			// 		this.select('Knowledge Base')
			// 		this.$router.push({path: '/frappedesk/knowledge-base'})
			// 	}
			// },
			// {
			// 	label: 'Reports',
			// 	icon: 'reports',
			// 	action: () => {
			// 		this.select('Reports')
			// 		this.$router.push({path: '/frappedesk/reports'})
			// 	}
			// },
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
					// {
					// 	label: 'Organisations',
					// 	action: () => {
					// 		this.select('Organisations')
					// 		// this.$router.push({path: '/frappedesk/organisations'})
					// 	}
					// }
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
			this.menuOptions.find(option => option.label == 'Ticketing').children.push(...[
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

		this.profileSettings = [
			{
				label: 'View Website',
				icon: 'external-link',
				style: 'text-gray-800',
				action: () => {
					window.location.replace('/')
				}
			},
			{
				label: 'Log out',
				icon: 'log-out',
				style: 'text-red-600',
				action: () => {
					this.user.logout()
				}
			}
		]

		// When the page is refreshed / opened the selected side bar option will  be set 
		this.syncSelectedMenuItemBasedOnRoute()
	},
	watch: {
		ticketFilter(newValue) {
			this.select(newValue)
		}
	},
	methods: {
		syncSelectedMenuItemBasedOnRoute() {
			const handleTicketFilterQueries = () => {
				const ticketFilterMap = {
					'assigned-to-me': 'Assigned Tickets',
					'unassigned': 'Unassigned Tickets'
				}
				if (ticketFilterMap[this.$route.query['menu-filter']]) {
					return ticketFilterMap[this.$route.query['menu-filter']]
				} else {
					// TODO: remove menu-filter parameter from router query
					return 'All Tickets'
				}
			}

			const routeMenuItemMap = {
				'frappedesk/tickets': 'All Tickets',
				'frappedesk/knowledge-base': 'Knowledge Base',
				'frappedesk/reports': 'Reports',
				'frappedesk/contacts': 'Contacts',
				'frappedesk/settings': 'Settings'
			}
			Object.keys(routeMenuItemMap).forEach(route => {
				if (this.$route.path.includes(route)) {
					let selectedMenuItem = routeMenuItemMap[route]
					if (routeMenuItemMap[route] == 'All Tickets' && this.$route.query['menu-filter']) {
						selectedMenuItem = handleTicketFilterQueries()
					}
					this.select(selectedMenuItem)
					return
				}
			})
		},
		select(label) {
			this.menuOptions.forEach(option => {
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
	}
}

</script>