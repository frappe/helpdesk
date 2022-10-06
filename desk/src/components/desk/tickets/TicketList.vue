<template>
	<div>
		<div
			@pointerenter="
				() => {
					showSelectAllCheckbox = true
				}
			"
			@pointerleave="
				() => {
					showSelectAllCheckbox = false
				}
			"
			class="bg-[#F7F7F7] group flex items-center h-[40px] text-base font-medium text-gray-500 py-[10px] px-[11px] rounded-[6px] select-none"
		>
			<div class="w-[37px] h-[14px]">
				<Input
					type="checkbox"
					@click="manager.selectAll()"
					:checked="manager.allItemsSelected"
					class="cursor-pointer mr-1 hover:visible"
					:class="
						manager.allItemsSelected || showSelectAllCheckbox
							? 'visible'
							: 'invisible'
					"
				/>
			</div>
			<div
				class="sm:w-1/12 flex flex-row items-center space-x-[7px] cursor-pointer"
				@click="manager.toggleOrderBy('name')"
			>
				<span>#</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="manager.options.order_by.split(' ')[0] === 'name'"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-7/12 flex flex-row items-center space-x-[6px] cursor-pointer"
				@click="manager.toggleOrderBy('subject')"
			>
				<span>Subject</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] === 'subject'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-3/12 flex flex-row items-center space-x-[6px] cursor-pointer"
				@click="manager.toggleOrderBy('status')"
			>
				<span>Status</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] === 'status'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-3/12 flex flex-row items-center space-x-[6px] cursor-pointer"
				@click="manager.toggleOrderBy('contact')"
			>
				<span>Created By</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] === 'contact'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-2/12 flex flex-row items-center space-x-[6px] cursor-pointer"
				@click="manager.toggleOrderBy('resolution_by')"
			>
				<span>Due In</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] ===
							'resolution_by'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-1/12 flex flex-row items-center space-x-[6px] cursor-pointer"
				@click="manager.toggleOrderBy('modified')"
			>
				<span>Modified</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] ===
							'modified'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-1/12 text-[11px] flex flex-row-reverse text-gray-500"
			>
				<span> {{ manager.totalCount }} </span>
			</div>
		</div>
		<div
			id="rows"
			class="flex flex-col overflow-scroll"
			:style="{
				height: viewportWidth > 768 ? 'calc(100vh - 112px)' : null,
			}"
		>
			<div v-if="manager.loading">
				<div v-for="n in 3" :key="n">
					<TicketListItemSkeleton
						:class="n == 0 ? 'mt-[9px] mb-[2px]' : 'my-[2px]'"
						class="my-[9px]"
					/>
				</div>
			</div>
			<div v-else>
				<div v-if="manager.list.length > 0">
					<div
						v-for="(ticket, index) in manager.list"
						:key="ticket.name"
					>
						<TicketListItem
							:class="
								index == 0 ? 'mt-[9px] mb-[2px]' : 'my-[2px]'
							"
							:ticket="ticket"
							@toggle-select="manager.select(ticket)"
							:selected="manager.itemSelected(ticket)"
						/>
					</div>
				</div>
				<div v-else>
					<div class="grid place-content-center h-48 w-full">
						<div>
							<CustomIcons
								name="empty-list"
								class="h-12 w-12 mx-auto mb-2"
							/>
							<div class="text-gray-500 mb-2">
								No tickets found
							</div>
						</div>
					</div>
				</div>
			</div>
			<div class="pb-2">
				<Button v-if="manager.hasNextPage" @click="manager.nextPage()">
					Load More
				</Button>
			</div>
		</div>
	</div>
</template>

<script>
import { ref, inject } from "vue"
import { Input } from "frappe-ui"
import TicketListItem from "@/components/desk/tickets/TicketListItem.vue"
import TicketListItemSkeleton from "@/components/desk/tickets/TicketListItemSkeleton.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "TicketList",
	props: ["manager"],
	components: {
		TicketListItem,
		TicketListItemSkeleton,
		CustomIcons,
		Input,
	},
	setup() {
		const showSelectAllCheckbox = ref(false)
		const viewportWidth = inject("viewportWidth")
		return {
			showSelectAllCheckbox,
			viewportWidth,
		}
	},
	unmounted() {
		this.$socket.off()
	},
}
</script>
