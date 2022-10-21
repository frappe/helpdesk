<template>
	<Avatar
		v-if="user"
		:label="user.full_name"
		:imageURL="user.user_image"
		v-bind="$attrs"
	/>
</template>
<script>
import { Avatar } from "frappe-ui"

export default {
	name: "UserAvatar",
	inheritAttrs: false,
	components: { Avatar },
	props: ["user"],
}
</script>
