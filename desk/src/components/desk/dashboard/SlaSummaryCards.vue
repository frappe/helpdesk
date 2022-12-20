<template>
	<div class="mt-8 ml-8 mb-8 mr-6">
		<div class="line-clamp-1 text-xl text-gray-900 font-semibold">
			SLA Summary
		</div>
		<div class="grid grid-cols-3 mt-8 mb-8 gap-4">
			<div
				class="flex flex-row items-center box-border h-[68px] p-4 border-2 rounded-md justify-between"
			>
				<div class="font-light text-xl text-[#74808B]">
					Avg. First Response time (hours)
				</div>
				<div class="font-medium text-[36px] text-[#505A62]">
					{{ averageFirstResponseTime }}
				</div>
			</div>
			<div
				class="flex flex-row items-center box-border h-[68px] p-4 border-2 rounded-md justify-between"
			>
				<div class="font-light text-xl text-[#74808B]">
					Avg. Resolution Time (hours)
				</div>
				<div class="font-medium text-[36px] text-[#505A62]">
					{{ averageResolutionTime }}
				</div>
			</div>
			<div
				class="flex flex-row items-center box-border h-[68px] p-4 border-2 rounded-md justify-between"
			>
				<div class="font-light text-xl text-[#74808B]">
					Resolution within SLA
				</div>
				<div class="font-semibold text-[36px] text-[#505A62]">
					{{ resolutionWithinSla }}
				</div>
			</div>
		</div>
	</div>
</template>

<script>
export default {
	name: "SlaSummaryCards",
	computed: {
		averageFirstResponseTime() {
			return this.$resources.averageFirstResponseTime.data
		},
		averageResolutionTime() {
			return this.$resources.averageResolutionTime.data
		},
		resolutionWithinSla() {
			return this.$resources.resolutionWithinSla.data
		},
	},
	resources: {
		averageFirstResponseTime() {
			return {
				method: "frappedesk.api.dashboard.average_first_response_time",
				auto: true,
			}
		},
		averageResolutionTime() {
			return {
				method: "frappedesk.api.dashboard.average_resolution_time",
				auto: true,
			}
		},
		resolutionWithinSla() {
			return {
				method: "frappedesk.api.dashboard.resolution_within_sla",
				auto: true,
			}
		},
	},
}
</script>

<style scoped></style>
