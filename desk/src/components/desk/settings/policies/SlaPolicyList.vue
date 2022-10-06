<template>
	<div>
		<div
			class="bg-[#F7F7F7] group flex items-center text-base font-medium text-gray-500 py-[10px] px-[11px] rounded-[6px] select-none"
		>
			<div class="w-[37px] h-[14px]">
				<Input
					type="checkbox"
					@click="manager.selectAll()"
					:checked="manager.allItemsSelected"
					role="button"
				/>
			</div>
			<div class="flex flex-row items-center group w-full">
				<div class="sm:w-10/12">Policy Name</div>
				<div class="sm:w-2/12" />
			</div>
		</div>
		<div
			id="rows"
			class="flex flex-col space-y-2 overflow-scroll"
			:style="{
				height: viewportWidth > 768 ? 'calc(100vh - 120px)' : null,
			}"
		>
			<div v-if="!manager.loading">
				<div v-if="manager.list.length > 0">
					<div
						v-for="(policy, index) in manager.list"
						:key="policy.name"
					>
						<SlaPolicyListItem
							:class="
								index == 0 ? 'mt-[9px] mb-[2px]' : 'my-[2px]'
							"
							:policy="policy"
							@toggle-select="manager.select(policy)"
							:selected="manager.itemSelected(policy)"
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
								No policies found
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
import { inject } from "vue"
import { Input } from "frappe-ui"
import SlaPolicyListItem from "@/components/desk/settings/policies/SlaPolicyListItem.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "SlaPolicyList",
	props: ["manager"],
	components: {
		SlaPolicyListItem,
		CustomIcons,
		Input,
	},
	setup() {
		const viewportWidth = inject("viewportWidth")
		return {
			viewportWidth,
		}
	},
}
</script>
