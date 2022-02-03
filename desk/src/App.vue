<template>
	<div>
		<div class="h-15">
			<NavBar/>
		</div>
		<div class="flex">
			<div class="w-20 pt-4">
				<SideBarMenu/>
			</div>
			<div class="w-screen pt-4 ml-5 mr-10">
				<keep-alive>
					<router-view />
				</keep-alive>
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
    provide: {
        viewportWidth: Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
    },
    componsnets: {
        NavBar,
        SideBarMenu
	},
    components: { NavBar, SideBarMenu }
}
</script>