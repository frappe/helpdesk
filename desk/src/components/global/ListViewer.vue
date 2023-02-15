<template>
	<div class="h-full">
		<slot name="body">
			<slot name="list-body">
				<div class="h-full">
					<slot name="top-section">
						<div
							class="flex flex-row w-full items-center h-[30px] mb-4 space-x-2"
						>
							<div class="shrink-0">
								<slot name="top-sub-section-1">
									<PresetFilters
										:ListTitle="options.listTitle"
										v-if="options.presetFilters"
									/>
								</slot>
							</div>
							<div class="w-full">
								<slot name="top-sub-section-2">
									<FilterBox v-if="options.filterBox" />
								</slot>
							</div>
							<div
								v-if="
									options.filterBox &&
									options.presetFilters &&
									manager.options.filters.length > 0
								"
							>
								<Button
									icon-left="layers"
									appearance="minimal"
									@click="
										() => {
											showSaveFiltersDialog = true
										}
									"
								>
									Save
								</Button>
								<SaveFiltersDialog
									v-model="showSaveFiltersDialog"
									@close="showSaveFiltersDialog = false"
								/>
							</div>
							<div class="shrink-0">
								<slot name="top-sub-section-3">
									<!-- Actions / Bulk actions -->
									<div
										v-if="
											Object.keys(manager.selectedItems)
												.length > 0
										"
									>
										<!-- Bulk Actions -->
										<slot
											name="bulk-actions"
											:selectedItems="
												manager.selectedItems
											"
										/>
									</div>
									<div v-else class="flex flex-row space-x-2">
										<!-- Actions -->
										<slot name="actions" />
										<slot name="primary-action">
											<!-- Add Item -->
											<Button
												appearance="primary"
												icon-left="plus"
												@click="$emit('add-item')"
											>
												{{
													options.name != null
														? `Add ${options.name}`
														: `Add ${manager.options.doctype}`
												}}
											</Button>
										</slot>
									</div>
								</slot>
							</div>
						</div>
					</slot>
					<div class="grow h-full">
						<table class="w-full table-auto border-separate border-spacing-y-2">
							<thead>
								<tr class="bg-gray-100 text-base text-gray-500 select-none">
									<th class="p-3 rounded-tl-md rounded-bl-md">
										<Input
											type="checkbox"
											@click="manager.selectAll"
											:checked="manager.allItemsSelected"
											class="cursor-pointer"
										/>
									</th>
									<th
										class="text-start last-of-type:rounded-tr-md last-of-type:rounded-br-md 
										font-normal hover:text-gray-600 cursor-pointer fill-gray-300"
										v-for="field in Object.keys(renderOptions.fields)"
										:key="field"
										@click="manager.toggleOrderBy(field)"
									>
										{{ renderOptions.fields[field].label }}
										<div class="inline-table">
											<CustomIcons
												v-show="sortArrowShow(field)"
												:name="sortArrowName()"
												class="h-1 fill-gray-400 stroke-transparent"
											/>
										</div>
									</th>
								</tr>
							</thead>
							<tbody>
								<tr
									v-for="item in manager.list"
									class="hover:bg-gray-50"
								>
									<td class="p-3 rounded-tl-md rounded-bl-md">
										<Input
											type="checkbox"
											@click="manager.select(item)"
											:checked="manager.itemSelected(item)"
											class="cursor-pointer"
										/>
									</td>
									<td
										v-for="field in Object.keys(renderOptions.fields)"
										:key="field"
										class="py-2 last-of-type:rounded-tr-md last-of-type:rounded-br-md last-of-type:pr-3"
									>
										<slot
											:name="
												'field-' + field
											"
											:field="field"
											:value="item[field]"
											:row="item"
										>
											{{
												item[field]
											}}
										</slot>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
					<div>
						<slot name="pagination">
							<div class="flex flex-row items-center h-[43px]">
								<ListPageController />
							</div>
						</slot>
					</div>
				</div>
			</slot>
		</slot>
	</div>
</template>

<script>
import { Dropdown, FeatherIcon } from "frappe-ui"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import PresetFilters from "@/components/global/PresetFilters.vue"
import FilterBox from "@/components/global/FilterBox.vue"
import ListPageController from "@/components/global/ListPageController.vue"
import SaveFiltersDialog from "@/components/global/SaveFiltersDialog.vue"
import { ref, computed, provide } from "vue"

export default {
	name: "ListViewer",
	components: {
		CustomIcons,
		Dropdown,
		FeatherIcon,
		FilterBox,
		ListPageController,
		PresetFilters,
		SaveFiltersDialog,
	},
	props: {
		options: {
			type: Object,
			default: () => ({}),
		},
	},
	inject: ["manager"],
	setup(props) {
		const showSaveFiltersDialog = ref(false)
		const renderOptions = computed(() => {
			const options = {
				fields: {},
				base: props.options.base || "12",
				filterBox: props.options.filterBox || false,
				presetFilters: props.options.presetFilters || false,
			}
			for (let i in props.options.fields) {
				options.fields[i] = {
					label: props.options.fields[i].label || i,
					width: props.options.fields[i].width || 1,
					priority: props.options.fields[i].priority || 5,
					align: props.options.fields[i].align || "left",
				}
			}
			return options
		})
		provide("renderOptions", renderOptions)
		return {
			showSaveFiltersDialog,
			renderOptions,
		}
	},
	methods: {
		sortArrowShow(field) {
			const [orderByField] = this.manager.options.order_by.split(" ");
			return orderByField === field;
		},
		sortArrowName() {
			const [_, sortOrder] = this.manager.options.order_by.split(" ");
			return sortOrder === "desc" ? "chevron-up" : "chevron-down";
		}
	}
}
</script>
