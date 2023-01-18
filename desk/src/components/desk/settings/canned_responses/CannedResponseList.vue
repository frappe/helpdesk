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
				<div class="sm:w-10/12">Title</div>
				<div class="sm:w-2/12">Author</div>
				<div class="sm:w-2/12"></div>
			</div>
		</div>
		<div
			id="rows"
			class="flex flex-col space-y-2 overflow-auto"
			:style="{
				height: viewportWidth > 768 ? 'calc(100vh - 120px)' : null,
			}"
		>
			<div v-if="!manager.loading">
				<div v-if="manager.list.length > 0">
					<div
						v-for="(canned_response, index) in manager.list"
						:key="canned_response.name"
					>
						<CannedResponseListItem
							:class="
								index == 0 ? 'mt-[9px] mb-[2px]' : 'my-[2px]'
							"
							:canned_response="canned_response"
							@toggle-select="manager.select(canned_response)"
							:selected="manager.itemSelected(canned_response)"
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
								No canned response found
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
import CannedResponseListItem from "@/components/desk/settings/canned_responses/CannedResponseListItem.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
export default {
	name: "CannedResponseList",
	props: ["manager"],
	components: {
		CannedResponseListItem,
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
