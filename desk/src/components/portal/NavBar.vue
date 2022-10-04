<template>
	<div class="py-4">
		<div class="container mx-auto">
			<div class="flex flex-wrap justify-between items-center">
				<div class="flex items-center">
					<a href="/"
						><CustomIcons name="company" class="max-h-10"
					/></a>
				</div>
				<div
					class="flex space-x-8 text-[14px] text-[#4C5A67] items-center"
				>
					<div v-for="item in navbarItems" :key="item.label">
						<Dropdown
							v-if="item.children.length > 0"
							:options="item.children"
						>
							<template v-slot="{ toggleDropdown }">
								<div
									class="flex flex-row space-x-2 items-center cursor-pointer"
									@click="toggleDropdown"
								>
									<span class="hover:text-[#2490ef]">{{
										item.label
									}}</span>
									<FeatherIcon
										name="chevron-down"
										class="h-4 w-4 stroke-black"
									/>
								</div>
							</template>
						</Dropdown>
						<a
							v-else
							:href="item.url"
							class="hover:text-[#2490ef]"
							v-html="item.label"
						/>
					</div>
					<Dropdown
						placement="right"
						:options="profileOptions"
						:dropdown-width-full="true"
					>
						<template v-slot="{ toggleDropdown }">
							<CustomAvatar
								v-if="user"
								@click="toggleDropdown"
								:label="user.username"
								class="cursor-pointer"
								size="xl"
								:imageURL="user.profile_image"
							/>
						</template>
					</Dropdown>
				</div>
			</div>
		</div>
	</div>
</template>
<script>
import { Dropdown, FeatherIcon } from "frappe-ui"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import CustomAvatar from "../global/CustomAvatar.vue"
import { inject } from "vue"

export default {
	name: "NavBar",
	components: {
		CustomIcons,
		CustomAvatar,
		Dropdown,
		FeatherIcon,
	},
	setup() {
		const user = inject("user")
		const ticketTemplates = inject("ticketTemplates")

		return { user, ticketTemplates }
	},
	resources: {
		navbarItems() {
			return {
				method: "frappedesk.api.website.navbar_items",
				auto: true,
			}
		},
	},
	computed: {
		navbarItems() {
			const parentItems = []
			if (this.$resources.navbarItems.data) {
				this.$resources.navbarItems.data.forEach((item) => {
					if (!item.parent_label) {
						item.children = []
						parentItems.push(item)
					}
				})
				this.$resources.navbarItems.data.forEach((item) => {
					if (item.parent_label) {
						item.handler = () => {
							window.location.href = item.url
						}
						parentItems
							.find((x) => x.label === item.parent_label)
							.children.push(item)
					}
				})
				return parentItems
			} else {
				return parentItems
			}
		},
		profileOptions() {
			return [
				{
					label: "My Account",
					handler: () => {
						window.location.href = "/me"
					},
				},
				{
					label: "Logout",
					handler: () => {
						this.user?.logout()
						window.location.href = "/support/login"
					},
				},
			]
		},
	},
}
</script>
