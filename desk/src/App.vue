<template>
	<div class="w-screen flex">
		<div class="w-15">
			<SideBarMenu />
		</div>
		<div class="flex-col w-full">
			<div class="h-15">
				<NavBar />
			</div>
			<div class="pt-1">
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
import NavBar from "./components/NavBar.vue";
import SideBarMenu from "./components/SideBarMenu.vue";

export default {
	name: "App",
	data() {
		return {
			viewportWidth: 0
		};
	},
	resources: {
		user() {
			return {
				'method': 'helpdesk.api.agent.get_user',
				auto: true,
				onSuccess: () => {
					this.$user.set(this.$resources.user.data);
				}
			}
		}
	},
	provide: {
		viewportWidth: Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
	},
	components: {
		NavBar,
		SideBarMenu,
	},
}
</script>