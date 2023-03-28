<template>
	<div class="p-5">
		<div class="flex">
			<div>Please login to access Helpdesk</div>
			<div class="ml-2">
				<Button @click="login">Login</Button>
			</div>
		</div>
	</div>
</template>

<script>
export default {
	name: "Login",
	methods: {
		login() {
			window.location.replace("/login")
		},
	},
}
</script>

<style></style>
