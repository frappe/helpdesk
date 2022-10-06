<template>
	<div>
		<img v-if="name == 'gmail'" src="@/assets/images/gmail.png" />
		<img v-if="name == 'outlook'" src="@/assets/images/outlook.png" />
		<img v-if="name == 'sendgrid'" src="@/assets/images/sendgrid.png" />
		<img v-if="name == 'sparkpost'" src="@/assets/images/sparkpost.webp" />
		<img v-if="name == 'yahoo'" src="@/assets/images/yahoo.png" />
	</div>
</template>

<script>
export default {
	name: "Images",
	props: {
		name: {
			type: String,
			required: true,
		},
	},
}
</script>
