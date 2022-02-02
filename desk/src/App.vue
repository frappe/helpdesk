<template>
	<div>
		<div class="h-20">

		</div>
		<div class="flex">
			<div class="w-20 pt-4"></div>
			<div class="w-screen pt-4 ml-5 mr-10">
				<keep-alive>
					<router-view />
				</keep-alive>
			</div>
		</div>
	</div>
</template>

<script>

export default {
	name: 'App',
	data() {
		return {
			viewportWidth: 0
		};
	},
	provide: {
		viewportWidth: Math.max(
			document.documentElement.clientWidth || 0,
			window.innerWidth || 0
		)
	},
}
</script>