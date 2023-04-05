<template>
	<div class="flex flex-col w-full">
		<AgentRelatedInfoTopPanel />
		<div v-if="relatedInfoToShow === 'tickets'" class="w-full px-4">
			<ListManager
				ref="miniTicketList"
				:options="{
					doctype: 'HD Ticket',
					fields: [
						'_assign',
						'status',
						'priority',
						'subject',
						'ticket_type',
						'name',
						'_seen',
					],
					limit: 20,
					order_by: 'modified desc',
					filters: {
						_assign: ['like', `%${agent}%`],
					},
				}"
			>
				<template #body>
					<ListViewer
						:options="{
							base: 12,
							fields: {
								name: {
									label: '#',
									width: '1',
								},
								subject: {
									label: 'Subject',
									width: '5',
								},
								status: {
									label: 'Status',
									width: '2',
								},
								ticket_type: {
									label: 'Type',
									width: '2',
								},
								priority: {
									label: 'Priority',
									width: '2',
									align: 'right',
								},
							},
						}"
						class="text-base h-[calc(100vh-9rem)] pt-4"
					>
						<template #top-section> <div></div> </template>
						<template #field-name="{ value }">
							<div class="text-xs text-gray-500">
								{{ value }}
							</div>
						</template>
						<template #field-subject="{ row }">
							<Subject :ticket="row" />
						</template>
						<template #field-status="{ value }">
							<TicketStatus :value="value" />
						</template>
						<template #field-priority="{ value }">
							<TicketPriority :value="value" />
						</template>
						<template #field-ticket_type="{ value }">
							<TicketType :value="value" />
						</template>
					</ListViewer>
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
import ListManager from "@/components/global/ListManager.vue"
import ListViewer from "@/components/global/ListViewer.vue"
import { FeatherIcon, Tooltip } from "frappe-ui"
import { ref } from "vue"
import TicketType from "@/components/global/ticket_list_item/TicketType.vue"
import TicketStatus from "@/components/global/ticket_list_item/TicketStatus.vue"
import TicketPriority from "@/components/global/ticket_list_item/TicketPriority.vue"
import Subject from "@/components/global/ticket_list_item/Subject.vue"

export default {
	name: "RelatedInfo",
	props: ["agent"],
	components: {
		AgentRelatedInfoTopPanel,
		FeatherIcon,
		Tooltip,
		ListManager,
		ListViewer,
		TicketType,
		TicketStatus,
		TicketPriority,
		Subject,
	},
	setup() {
		const relatedInfoToShow = ref("tickets")

		return {
			relatedInfoToShow,
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
