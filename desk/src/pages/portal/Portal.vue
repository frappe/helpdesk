<template>
	<div>
		<div class="h-15 border-b">
			<NavBar />
		</div>
		<div class="mb-10">
			<router-view v-slot="{ Component }" :key="$route.fullPath">
				<component :is="Component" />
			</router-view>
		</div>
	</div>
</template>

<script>
import NavBar from "@/components/portal/NavBar.vue"

export default {
	name: "Portal",
	components: { NavBar },
}
</script>
