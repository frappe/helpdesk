<template>
	<div
		class="flex flex-col border-r pt-[23px]"
		:style="{ height: viewportWidth > 768 ? 'calc(100vh)' : null }"
	>
		<div
			class="mb-[18.4px] cursor-pointer items-baseline pl-[22px] pr-[22px] w-fit flex flex-row space-x-[6px]"
		>
			<CustomIcons
				name="frappedesk"
				class="h-[15.88px]"
				@click="
					() => {
						$router.push({ path: '/frappedesk/tickets' })
					}
				"
			/>
			<div class="text-[10px] font-normal text-gray-700">
				v{{ fdVersion }}
			</div>
		</div>
		<div class="mx-[8px] mb-auto select-none space-y-[4px] text-gray-800">
			<div v-for="option in menuOptions" :key="option.label">
				<div
					class="pl-1 group cursor-pointer rounded-[6px] stroke-gray-600 hover:bg-gray-200"
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
					<div class="flex items-center py-[5.5px]">
						<div class="w-[24px]">
							<CustomIcons
								:name="option.icon"
								class="ml-[8px] h-[14px] w-[14px]"
							/>
						</div>
						<span class="ml-[6px] grow text-[13px]">{{
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
								class="group flex cursor-pointer items-center rounded-[8px] py-[6.25px] hover:bg-gray-200"
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
										class="mr-[10px] text-[11px] font-normal text-gray-500"
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
			<div class="mx-[8px] flex flex-col pb-[17px]">
				<div
					v-if="showProfileSettings"
					class="h-50 z-50 rounded-[6px] bg-white px-[7px] py-[6px] shadow-md"
				>
					<div v-for="item in profileSettings" :key="item.label">
						<div
							class="flex cursor-pointer flex-row items-center space-x-[10px] rounded-[8px] px-[13px] py-[5px] text-base font-normal hover:bg-gray-100"
							:class="item.style"
							@click="item.action()"
						>
							<CustomIcons
								v-if="item.customIcon"
								class="h-[16px] w-[16px]"
								:name="item.customIcon"
							/>
							<FeatherIcon
								v-else
								class="h-[16px] w-[16px]"
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
					class="flex cursor-pointer flex-row items-center space-x-[7px] rounded-[6px] px-[14px] py-[12px] hover:bg-gray-100"
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
							class="truncate text-[11px] font-normal"
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
								class="h-[50px] border-y"
							>
								<td class="w-[170px] border-r px-4">
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
				icon: "knowledge-base",
				to: {
					path: "/frappedesk/kb",
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
				label: "Keyboard Shortcuts",
				icon: "command",
				style: "text-gray-800",
				action: () => {
					this.showKeyboardShortcuts = true
				},
			},
			{
				label: "Go to customer portal",
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
				"frappedesk/tickets": "Tickets",
				"frappedesk/kb": "Knowledge Base",
				"frappedesk/reports": "Reports",
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
