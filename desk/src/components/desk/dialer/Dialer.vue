<template>
	<div v-if="shown" class="absolute bottom-11 right-0 m-4">
		<div class="w-[20rem] rounded-lg border bg-white p-3 shadow-md">
			<div class="flex flex-col space-y-3">
				<div
					class="flex flex-col w-full bg-gray-50 rounded-lg p-4 space-y-2"
				>
					<div
						class="flex flex-col w-full items-center border-b py-4 space-y-2"
					>
						<Avatar size="lg" label="Contact Id" />
						<div>Contact Name</div>
					</div>
					<div
						class="flex flex-row items-center justify-between w-full text-base"
					>
						<div>Reference Ticket</div>
						<Button icon="arrow-up-right" appearance="minimal" />
					</div>
				</div>
				<div
					class="flex flex-row bg-gray-100 rounded-lg justify-between items-center p-2"
				>
					<div class="text-base">Time: 1:27</div>
					<Button icon="phone-off" appearance="danger" />
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Avatar } from "frappe-ui"

export default {
	name: "Dialer",
	props: {},
	components: {
		Avatar,
	},
	mounted() {
		this.shown = true
	},
	data() {
		return {
			shown: false,
		}
	},
}
</script>
