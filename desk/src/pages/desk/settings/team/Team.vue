<template>
	<div class="flex flex-col">
		<TeamInfo :teamId="teamId" />
	</div>
</template>

<script>
import TeamInfo from "@/components/desk/settings/teams/TeamInfo.vue"
export default {
	name: "Team",
	props: ["teamId"],
	components: {
		TeamInfo,
	},
}
</script>
