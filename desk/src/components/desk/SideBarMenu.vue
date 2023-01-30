<template>
	<div
		class="flex flex-col border-r pt-6"
		:style="{ height: viewportWidth > 768 ? 'calc(100vh)' : null }"
	>
		<div
			class="mb-[18.4px] cursor-pointer items-baseline pl-5 pr-6 w-fit flex flex-row space-x-[6px]"
		>
			<CustomIcons
				name="frappedesk"
				class="h-4"
				@click="
					() => {
						$router.push({ path: '/frappedesk/dashboard' })
					}
				"
			/>
			<div class="text-xs font-normal text-gray-700">
				v{{ fdVersion }}
			</div>
		</div>
		<div class="mx-[8px] mb-auto select-none space-y-[4px] text-gray-800">
			<div v-for="option in menuOptions" :key="option.label">
				<div
					class="pl-1 group cursor-pointer rounded-md stroke-gray-600 hover:bg-gray-200"
					:class="option.selected ? 'bg-gray-100' : ''"
					@click="
						() => {
							if (option.children) {
								option.children
									? (option.expanded = !option.expanded)
									: {}
							} else if (option.to) {
								$router.push(option.to)
							}
						}
					"
				>
					<div class="flex items-center py-1.5">
						<div class="w-6">
							<CustomIcons
								:name="option.icon"
								class="ml-[8px] h-3.5 w-3.5"
							/>
						</div>
						<span class="ml-[6px] grow text-base">{{
							option.label
						}}</span>
					</div>
				</div>
				<div v-if="option.children && option.expanded" class="mt-[4px]">
					<div class="space-y-[4px]">
						<div
							v-for="childOption in option.children"
							:key="childOption.label"
						>
							<router-link
								class="group flex cursor-pointer items-center rounded-lg py-1.5 hover:bg-gray-200"
								:class="
									childOption.selected ? 'bg-gray-200' : ''
								"
								:to="
									childOption.to
										? {
												path: childOption.to.path,
												query: childOption.to.query
													? childOption.to.query()
													: {},
										  }
										: {}
								"
							>
								<div
									class="flex w-full flex-row items-center justify-between pl-[52px]"
								>
									<div class="text-base">
										{{ childOption.label }}
									</div>
									<div
										class="mr-[10px] text-xs font-normal text-gray-500"
									>
										{{ childOption.extra }}
									</div>
								</div>
							</router-link>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div>
			<div class="mx-[8px] flex flex-col pb-4">
				<div
					v-if="showProfileSettings"
					class="h-50 z-50 rounded-md bg-white px-2 py-1.5 shadow-md"
				>
					<div v-for="item in profileSettings" :key="item.label">
						<div
							class="flex cursor-pointer flex-row items-center space-x-[10px] rounded-lg px-3 py-1.5 text-base font-normal hover:bg-gray-100"
							:class="item.style"
							@click="item.action()"
						>
							<CustomIcons
								v-if="item.customIcon"
								class="h-4 w-4"
								:name="item.customIcon"
							/>
							<FeatherIcon
								v-else
								class="h-4 w-4"
								:name="item.icon"
							/>
							<span>{{ item.label }}</span>
						</div>
					</div>
				</div>
				<div
					@click="
						() => {
							showProfileSettings = !showProfileSettings
						}
					"
					v-on-outside-click="
						() => {
							showProfileSettings = false
						}
					"
					class="flex cursor-pointer flex-row items-center space-x-[7px] rounded-md px-3.5 py-3 hover:bg-gray-100"
					:class="showProfileSettings ? 'bg-gray-100' : ''"
				>
					<div>
						<CustomAvatar
							:label="user.username"
							class="cursor-pointer"
							size="lg"
							v-if="user"
							:imageURL="user.profile_image"
						/>
					</div>
					<div class="flex max-w-[150px] flex-col text-gray-700">
						<a
							:title="
								user.agent ? user.agent.agent_name : user.user
							"
							class="truncate text-base font-medium"
							>{{
								user.agent ? user.agent.agent_name : user.user
							}}</a
						>
						<a
							:title="user.user"
							class="truncate text-xs font-normal"
							>{{ user.user }}</a
						>
					</div>
				</div>
			</div>
		</div>
		<Dialog
			:options="{ title: 'Keyboard Shortcuts' }"
			v-model="showKeyboardShortcuts"
		>
			<template #body-content>
				<div class="py-5 text-base">
					<table class="w-full table-fixed border-collapse border">
						<tbody>
							<tr
								v-for="shortcut in keyboardShortcuts"
								:key="shortcut.label"
								class="h-12 border-y"
							>
								<td class="w-44 border-r px-4">
									<span
										class="rounded bg-gray-100 p-1.5 text-gray-500 shadow shadow-gray-400"
									>
										{{ shortcut.sequence }}
									</span>
								</td>
								<td class="px-4">{{ shortcut.label }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { Dropdown, FeatherIcon } from "frappe-ui"
import CustomAvatar from "@/components/global/CustomAvatar.vue"
import { inject, ref } from "vue"

export default {
	name: "SideBarMenu",
	components: {
		CustomIcons,
		Dropdown,
		CustomAvatar,
		FeatherIcon,
	},
	setup() {
		const isMac = ref(navigator.userAgent.indexOf("Mac OS X") != -1)
		const keyboardShortcuts = ref([
			{
				sequence: isMac ? "⌃ + ⌥ + R" : "Ctrl + Alt + R",
				label: "Mark status of ticket as Replied",
			},
			{
				sequence: isMac ? "⌃ + ⌥ + E" : "Ctrl + Alt + E",
				label: "Mark status of ticket as Resolved",
			},
			{
				sequence: isMac ? "⌃ + ⌥ + C" : "Ctrl + Alt + C",
				label: "Mark status of ticket as Closed",
			},
		])

		const showKeyboardShortcuts = ref(false)
		const viewportWidth = inject("viewportWidth")

		const user = inject("user")

		const iconHeight = ref(30)
		const iconWidth = ref(30)

		const menuOptions = ref()
		const profileSettings = ref()
		const showProfileSettings = ref(false)

		return {
			showKeyboardShortcuts,
			keyboardShortcuts,
			viewportWidth,
			user,
			iconHeight,
			iconWidth,
			menuOptions,
			profileSettings,
			showProfileSettings,
		}
	},
	mounted() {
		this.menuOptions = [
			{
				label: "Dashboard",
				icon: "dashboard",
				to: {
					path: "/frappedesk/dashboard",
				},
			},
			{
				label: "Tickets",
				icon: "ticket",
				to: {
					path: "/frappedesk/tickets",
				},
			},
			{
				label: "Knowledge Base",
				icon: "kb-articles",
				to: {
					path: "/frappedesk/kb",
				},
			},
			{
				label: "Customers",
				icon: "customer",
				to: {
					path: "/frappedesk/customers",
				},
			},
			{
				label: "Contacts",
				icon: "customers",
				to: {
					path: "/frappedesk/contacts",
				},
			},
			{
				label: "Settings",
				icon: "settings",
				to: {
					path: "/frappedesk/settings",
				},
			},
		]

		this.profileSettings = [
			{
				label: "Shortcuts",
				icon: "command",
				style: "text-gray-800",
				action: () => {
					this.showKeyboardShortcuts = true
				},
			},
			{
				label: "Customer portal",
				customIcon: "external-link",
				style: "text-gray-800",
				action: () => {
					window.open("/support/tickets", "_blank")
				},
			},
			{
				label: "Log out",
				customIcon: "log-out",
				style: "text-red-600",
				action: () => {
					this.user.logout()
				},
			},
		]

		this.syncSelectedMenuItemBasedOnRoute()
	},
	watch: {
		$route() {
			this.syncSelectedMenuItemBasedOnRoute()
		},
	},
	computed: {
		fdVersion() {
			if (this.$resources.fdeskVersion.loading) return ""
			return this.$resources.fdeskVersion.data.frappedesk.version
		},
	},
	methods: {
		syncSelectedMenuItemBasedOnRoute() {
			const routeMenuItemMap = {
				"frappedesk/dashboard": "Dashboard",
				"frappedesk/tickets": "Tickets",
				"frappedesk/kb": "Knowledge Base",
				"frappedesk/reports": "Reports",
				"frappedesk/customers": "Customers",
				"frappedesk/contacts": "Contacts",
				"frappedesk/settings": "Settings",
			}
			Object.keys(routeMenuItemMap).forEach((route) => {
				if (this.$route.path.includes(route)) {
					let selectedMenuItem = routeMenuItemMap[route]
					this.select(selectedMenuItem)
					return
				}
			})
		},
		select(label) {
			this.menuOptions.forEach((option) => {
				if (option.children) {
					option.children.forEach((childOption) => {
						childOption.selected = childOption.label == label
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
			})
		},
	},
	resources: {
		fdeskVersion() {
			return {
				method: "frappe.utils.change_log.get_versions",
				auto: true,
			}
		},
	},
}
</script>
