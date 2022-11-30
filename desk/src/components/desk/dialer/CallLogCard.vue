<template>
	<div
		v-if="callLog"
		class="flex flex-col my-[16px] bg-gray-100 rounded-[6px] p-[10px] text-base"
	>
		<div class="flex flex-row justify-between">
			<div>
				<div>{{ `From: ${callLog.agent_ref}` }}</div>
				<div>{{ `To: ${callLog.to}` }}</div>
				<div>{{ `Status: ${callLog.status}` }}</div>
			</div>
			<div class="text-gray-500 font-normal text-[12px]">
				{{ $dayjs.longFormating($dayjs(callLog.creation).fromNow()) }}
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"

export default {
	name: "CallLogCard",
	props: ["callLog"],
	components: {
		FeatherIcon,
	},
}
</script>
