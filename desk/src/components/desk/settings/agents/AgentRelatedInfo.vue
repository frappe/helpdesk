<template>
	<div class="flex flex-col w-full">
		<AgentRelatedInfoTopPanel />
		<div
			v-if="relatedInfoToShow === 'tickets'"
			class="w-full max-w-full grow-0"
		>
			<ListManager
				ref="miniTicketList"
				:options="{
					doctype: 'Ticket',
					fields: ['subject', 'ticket_type', 'status', '_seen'],
					limit: 50,
					order_by: 'modified desc',
					filters: {
						_assign: ['like', `%${agent}%`],
					},
					route_query_pagination: true,
				}"
			>
				<template #body="{ manager }">
					<div>
						<MiniTicketList
							class="overflow-y-scroll"
							:style="{
								height:
									viewportWidth > 768
										? 'calc(100vh - 135.5px)'
										: null,
							}"
							:manager="manager"
						/>
						<ListPageController :manager="manager" />
					</div>
				</template>
			</ListManager>
		</div>
		<div v-else class="h-full w-full flex max-w-full grow-0">
			<div class="mx-auto my-auto text-base font-normal">
				Comming Soon
			</div>
		</div>
	</div>
</template>

<script>
import AgentRelatedInfoTopPanel from "./AgentRelatedInfoTopPanel.vue"
import MiniTicketList from "@/components/desk/global/MiniTicketList.vue"
import ListManager from "@/components/global/ListManager.vue"
import ListPageController from "@/components/global/ListPageController.vue"
import { ref, inject } from "vue"

export default {
	name: "RelatedInfo",
	props: ["agent"],
	components: {
		AgentRelatedInfoTopPanel,
		MiniTicketList,
		ListManager,
		ListPageController,
	},
	setup() {
		const relatedInfoToShow = ref("tickets")
		const viewportWidth = inject("viewportWidth")

		return {
			relatedInfoToShow,
			viewportWidth,
		}
	},
	mounted() {
		this.$event.on(
			"agent-related-info-top-panel-selection-change",
			(selection) => {
				this.relatedInfoToShow = selection
			}
		)
	},
	unmounted() {
		this.$event.off("agent-related-info-top-panel-selection-change")
	},
}
</script>

<style></style>
