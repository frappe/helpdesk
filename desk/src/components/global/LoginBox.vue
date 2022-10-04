<template>
	<div class="h-full pt-4 sm:pt-16">
		<div>
			<div class="flex">
				<div class="mx-auto h-4 w-auto">
					<CustomIcons name="frappedesk" class="`w-5 h-5" />
				</div>
			</div>
			<div
				class="sm:w-0112 mx-auto bg-white px-4 py-8 sm:mt-6 sm:w-96 sm:rounded-lg sm:px-10 sm:shadow-xl"
			>
				<div class="mb-6 text-center">
					<span class="text-lg">{{ title }}</span>
				</div>
				<slot></slot>
			</div>
		</div>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "LoginBox",
	props: ["title"],
	components: {
		CustomIcons,
	},
	methods: {
		redirectForFrappeioAuth() {
			// TODO: ref (https://github.com/frappe/press/commit/f38b26dca5ea44c9b57de37a0162f9707356a903)
			window.location = "/f-login"
		},
	},
}
</script>
