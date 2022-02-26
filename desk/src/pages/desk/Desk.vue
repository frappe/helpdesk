<template>
	<div v-if="user.isLoggedIn()" class="w-screen flex">
		<div class="w-15">
			<SideBarMenu />
		</div>
		<div class="flex-col w-full">
			<div class="h-15">
				<NavBar />
			</div>
			<div>
				<router-view v-slot="{ Component }">
					<keep-alive>
						<component :is="Component" />
					</keep-alive>
				</router-view>
			</div>
		</div>
	</div>
</template>
<script>
import NavBar from "@/components/desk/NavBar.vue"
import SideBarMenu from "@/components/desk/SideBarMenu.vue"
import { inject } from 'vue'

export default {
	name: "Desk",
	components: {
		NavBar,
		SideBarMenu,
	},
	setup() {
		const user = inject('user')

		return { user }
	}
}
</script>