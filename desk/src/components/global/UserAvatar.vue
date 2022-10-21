<template>
	<Avatar :label="fulName" :imageURL="userImage" v-bind="$attrs" />
</template>
<script>
import { Avatar } from "frappe-ui"

export default {
	name: "UserAvatar",
	inheritAttrs: false,
	components: { Avatar },
	props: ["fullName", "userImage"],
}
</script>
