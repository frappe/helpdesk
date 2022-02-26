<template>
	<router-view v-slot="{ Component }">
		<component :is="Component" />
	</router-view>
</template>

<script>
export default {
	name: "App",
}
</script>