<template>
	<div class="flex flex-col w-full">
		<AgentRelatedInfoTopPanel />
		<div v-if="relatedInfoToShow === 'tickets'" class="w-full px-4 h-full">
			<ListManager
				ref="miniTicketList"
				:options="{
					doctype: 'Ticket',
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
				<template #body="{ manager }">
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
						class="text-base h-[87vh] pt-4"
					>
						<template #top-section> <div></div> </template>
						<template #field-name="{ value }">
							<div class="text-xs text-gray-500">
								{{ value }}
							</div>
						</template>
						<template #field-subject="{ value, row }">
							<router-link
								:to="{
									path: `/frappedesk/tickets/${row.name}`,
								}"
								role="button"
								class="line-clamp-1 hover:text-gray-900 text-gray-600"
								:class="{
									'font-semibold text-gray-900': !(
										JSON.parse(row._seen) || []
									).includes(user.user),
								}"
							>
								{{ value }}
							</router-link>
						</template>
						<template #field-status="{ value }">
							<div class="flex flex-row items-center space-x-1">
								<FeatherIcon
									v-if="value != 'Open'"
									:name="
										{
											Closed: 'lock',
											Resolved: 'check',
											Replied: 'corner-up-left',
										}[value]
									"
									class="stroke-gray-600 w-[12px] h-[12px] mx-[2px]"
								/>
								<CustomIcons
									v-else
									name="comment"
									class="w-[16px] h-[16px] stroke-green-600"
								/>
								<div
									class="text-base font-normal"
									:class="{
										'text-green-600': value == 'Open',
										'text-gray-600': value != 'Open',
									}"
								>
									{{ value }}
								</div>
							</div>
						</template>
						<template #field-priority="{ value }">
							<div class="flex flex-row items-center space-x-1">
								<div
									class="text-sm font-semibold px-2 border rounded-lg"
									:class="{
										'text-green-500 bg-green-100 border-green-500':
											value == 'Low',
										'text-yellow-500 bg-yellow-100 border-yellow-500':
											value == 'Medium',
										'text-orange-500 bg-orange-100 border-orange-500':
											value == 'High',
										'text-red-500 bg-red-100 border-red-500':
											value == 'Urgent',
									}"
								>
									{{ value.toLowerCase() }}
								</div>
							</div>
						</template>
						<template #field-ticket_type="{ value }">
							<div v-if="value" class="text-gray-600">
								{{ value }}
							</div>
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
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { FeatherIcon, Tooltip } from "frappe-ui"
import { ref, inject } from "vue"

export default {
	name: "RelatedInfo",
	props: ["agent"],
	components: {
		AgentRelatedInfoTopPanel,
		FeatherIcon,
		Tooltip,
		CustomIcons,
		ListManager,
		ListViewer,
	},
	inject: ["user"],
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
