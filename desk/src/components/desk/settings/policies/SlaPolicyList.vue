<template>
	<div>
		<div
			class="bg-[#F7F7F7] group flex items-center text-base font-medium text-gray-500 py-2.5 px-2.5 rounded-md select-none"
		>
			<div class="w-9 h-3.5">
				<Input
					type="checkbox"
					@click="manager.selectAll()"
					:checked="manager.allItemsSelected"
					role="button"
				/>
			</div>
			<div class="flex flex-row items-center group w-full">
				<div class="sm:w-10/12">Policy Name</div>
				<div class="sm:w-2/12">
					<div class="flex flex-row-reverse">Active</div>
				</div>
			</div>
		</div>
		<div
			id="rows"
			class="flex flex-col space-y-2 overflow-y-auto"
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
								index == 0 ? 'mt-2.5 mb-0.5' : 'mt-0.5'
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
