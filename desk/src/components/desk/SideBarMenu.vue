<template>
	<div class="flex flex-col border-r pt-[23px]" :style="{ height: viewportWidth > 768 ? 'calc(100vh)' : null }">
		<div class="mb-[38.4px] pl-[22px] cursor-pointer">
			<CustomIcons name="frappedesk" class="w-[67.84px] h-[16.6px]" @click="() => {$router.push({path: '/frappedesk/tickets'})}"/>
		</div>
		<div class="mb-auto space-y-[4px] select-none mx-[8px] text-gray-800">
			<div v-for="option in menuOptions" :key="option.label">
				<div
					class="group stroke-gray-600 rounded-[8px] cursor-pointer hover:bg-gray-200"
					:class="option.selected ? 'bg-gray-200' : ''"
					@click="() => {
						if (option.children) {
							option.children ? option.expanded = !option.expanded : {}
						} else if(option.to) {
							$router.push(option.to)
						}
					}"
				>
					<div class="pl-[8px] py-[5.5px] flex items-center">
						<div class="w-[14px]">
							<FeatherIcon v-if="option.children" class="h-[14px] w-[14px] stroke-gray-600" :name="option.expanded ? 'chevron-up' : 'chevron-down'" />
						</div>
						<div class="w-[24px]">
							<CustomIcons :name="option.icon" class="ml-[8px] h-[14px] w-[14px]"/>
						</div>
						<span class="grow ml-[6px] text-[14px]">{{ option.label }}</span>
					</div>
				</div>
				<div v-if="option.children && option.expanded" class="mt-[4px]">
					<div class="space-y-[4px]">
						<div v-for="childOption in option.children" :key="childOption.label">
							<router-link 
								class="group py-[6.25px] rounded-[8px] flex items-center cursor-pointer hover:bg-gray-200"
								:class="childOption.selected ? 'bg-gray-200' : ''"
								:to="childOption.to ? {path: childOption.to.path, query: childOption.to.query ? childOption.to.query() : {}}: {}"
							>
								<div class="pl-[52px] w-full flex flex-row items-center justify-between">
									<div class="text-base">
										{{ childOption.label }}
									</div>
									<div class="text-[11px] font-normal mr-[10px] text-gray-500">{{ childOption.extra }}</div>
								</div>
							</router-link>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div>
			<div class="mx-[8px] pb-[17px] flex flex-col">
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
import { Dropdown, FeatherIcon, call } from 'frappe-ui'
import CustomAvatar from "@/components/global/CustomAvatar.vue"
import { inject, ref } from 'vue'

export default {
	name: 'SideBarMenu',
	components: {
		CustomIcons,
		Dropdown,
		CustomAvatar,
		FeatherIcon
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		
		const user = inject('user')

		const iconHeight = ref(30)
		const iconWidth = ref(30)

		const menuOptions = ref()
		const profileSettings = ref()
		const showProfileSettings = ref(false)

		const updateSidebarTicketCount = inject('updateSidebarTicketCount')

		const sideBarFilterMap = inject('sideBarFilterMap')
		const ticketSideBarFilter = inject('ticketSideBarFilter')

		return { 
			viewportWidth, 
			user, 
			iconHeight, 
			iconWidth, 
			menuOptions, 
			profileSettings, 
			showProfileSettings, 
			updateSidebarTicketCount, 
			ticketSideBarFilter,
			sideBarFilterMap
		}
	},
	mounted() {
		this.menuOptions = [
			{
				label: 'Tickets',
				icon: 'ticket',
				expanded: true,
				children: [],
			},
			{
				label: 'Contacts',
				icon: 'customers',
				children: [
					{
						label: 'Contacts',
						to: {
							path: '/frappedesk/contacts',
						}
					},
				],
			},
			{
				label: 'Settings',
				icon: 'settings',
				to: {
					path: '/frappedesk/settings',
				},
			}
		]

		if (this.user.agent) {
			this.ticketSideBarFilter = 'my-open-tickets'

			this.menuOptions.find(option => option.label == 'Tickets').children.push(...[
				{
					label: 'My Open Tickets',
					to: {
						path: '/frappedesk/tickets',
						query: () => {
							return {
								...this.$route.query,
								menu_filter: 'my-open-tickets',
								page: 1
							}
						}
					}
				},
				{
					label: 'My Replied Tickets',
					to: {
						path: '/frappedesk/tickets',
						query: () => {
							return {
								...this.$route.query,
								menu_filter: 'my-replied-tickets',
								page: 1
							}
						}
					},
				},
				{
					label: 'My Resolved Tickets',
					to: {
						path: '/frappedesk/tickets',
						query: () => {
							return {
								...this.$route.query,
								menu_filter: 'my-resolved-tickets',
								page: 1
							}
						}
					},
				},
				{
					label: 'My Closed Tickets',
					to: {
						path: '/frappedesk/tickets',
						query: () => {
							return {
								...this.$route.query,
								menu_filter: 'my-closed-tickets',
								page: 1
							}
						}
					},
				},
			])
		}

		this.menuOptions.find(option => option.label == 'Tickets').children.push(...[
			{
				label: 'All Tickets',
				to: {
					path: '/frappedesk/tickets',
					query: () => {
						return {
							...this.$route.query,
							menu_filter: 'all',
							page: 1
						}
					}
				},
			},
		])

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

		this.syncSideBarTicketFilter()
		this.syncSelectedMenuItemBasedOnRoute()

		this.updateSidebarTicketCount = this.updateTicketCount
	},
	watch: {
		$route() {
			this.syncSideBarTicketFilter()
			this.syncSelectedMenuItemBasedOnRoute()
		}
	},
	resources: {
		myOpenTicketsCount() {
			return {
				method: 'frappe.client.get_count',
				params: {
					doctype: 'Ticket',
					filters: {status: ['=', 'Open'], _assign: ['like', `%${this.user.agent.name}%`]}
				},
				auto: true,
				onSuccess(count) {
					this.menuOptions.find(option => option.label == 'Tickets').children[0].extra = count
				}
			}
		},
		myRepliedTicketsCount() {
			return {
				method: 'frappe.client.get_count',
				params: {
					doctype: 'Ticket',
					filters: {status: ['=', 'Replied'], _assign: ['like', `%${this.user.agent.name}%`]}
				},
				auto: true,
				onSuccess(count) {
					this.menuOptions.find(option => option.label == 'Tickets').children[1].extra = count
				}
			}
		}
	},
	methods: {
		updateTicketCount() {
			this.$resources.myOpenTicketsCount.fetch()
			this.$resources.myRepliedTicketsCount.fetch()
		},
		syncSideBarTicketFilter() {
			this.ticketSideBarFilter = this.$route.name === 'DeskTickets' ? this.$route.query.menu_filter : this.ticketSideBarFilter
		},
		syncSelectedMenuItemBasedOnRoute() {
			const handleTicketFilterQueries = () => {
				if (this.sideBarFilterMap[this.ticketSideBarFilter]) {
					return this.sideBarFilterMap[this.ticketSideBarFilter]
				} else {
					return 'All Tickets'
				}
			}

			const routeMenuItemMap = {
				'frappedesk/tickets': 'Tickets',
				'frappedesk/knowledge-base': 'Knowledge Base',
				'frappedesk/reports': 'Reports',
				'frappedesk/contacts': 'Contacts',
				'frappedesk/settings': 'Settings'
			}
			Object.keys(routeMenuItemMap).forEach(route => {
				if (this.$route.path.includes(route)) {
					let selectedMenuItem = routeMenuItemMap[route]
					if (routeMenuItemMap[route] == 'Tickets') {
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