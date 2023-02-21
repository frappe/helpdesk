<template>
	<div class="h-full">
		<div
			v-if="isLoading"
			class="flex h-full w-full justify-center align-middle"
		>
			<LoadingIndicator class="w-8 text-blue-600" />
		</div>
		<div v-else class="h-full">
			<slot name="body">
				<slot name="list-body">
					<div class="h-full">
						<div class="h-full">
							<slot name="top-section">
								<div
									class="mb-4 flex h-[30px] w-full flex-row items-center space-x-2"
								>
									<div class="shrink-0">
										<slot name="top-sub-section-1">
											<PresetFilters
												v-if="options.presetFilters"
												:list-title="options.listTitle"
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
													showSaveFiltersDialog = true;
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
											<div v-if="Object.keys(manager.selectedItems).length > 0">
												<!-- Bulk Actions -->
												<slot
													name="bulk-actions"
													:selected-items="manager.selectedItems"
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
							<div class="h-full grow">
								<table
									class="w-full table-auto border-separate border-spacing-y-2"
								>
									<thead>
										<tr class="select-none bg-gray-100 text-base text-gray-500">
											<th class="rounded-l-md p-3">
												<Input
													type="checkbox"
													:checked="manager.allItemsSelected"
													class="cursor-pointer"
													@click="manager.selectAll"
												/>
											</th>
											<th
												v-for="field in Object.keys(renderOptions.fields)"
												:key="field"
												class="cursor-pointer fill-gray-300 text-start font-normal last-of-type:rounded-r-md hover:text-gray-600"
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
										<tr v-for="item in manager.list" class="hover:bg-gray-50">
											<td class="rounded-l-md p-3">
												<Input
													type="checkbox"
													:checked="manager.itemSelected(item)"
													class="cursor-pointer"
													@click="manager.select(item)"
												/>
											</td>
											<td
												v-for="field in Object.keys(renderOptions.fields)"
												:key="field"
												class="py-2 last-of-type:rounded-r-md last-of-type:pr-3"
											>
												<slot
													:name="'field-' + field"
													:field="field"
													:value="item[field]"
													:row="item"
												>
													{{ item[field] }}
												</slot>
											</td>
										</tr>
									</tbody>
								</table>
							</div>
							<div>
								<slot name="pagination">
									<div class="flex h-[43px] flex-row items-center">
										<ListPageController />
									</div>
								</slot>
							</div>
						</div>
					</div>
				</slot>
			</slot>
		</div>
	</div>
</template>

<script>
import { Dropdown, FeatherIcon, LoadingIndicator } from "frappe-ui";
import CustomIcons from "@/components/desk/global/CustomIcons.vue";
import PresetFilters from "@/components/global/PresetFilters.vue";
import FilterBox from "@/components/global/FilterBox.vue";
import ListPageController from "@/components/global/ListPageController.vue";
import SaveFiltersDialog from "@/components/global/SaveFiltersDialog.vue";
import { ref, computed, provide } from "vue";

export default {
	name: "ListViewer",
	components: {
		CustomIcons,
		Dropdown,
		FeatherIcon,
		FilterBox,
		ListPageController,
		LoadingIndicator,
		PresetFilters,
		SaveFiltersDialog,
	},
	inject: ["manager"],
	props: {
		options: {
			type: Object,
			default: () => ({}),
		},
	},
	setup(props) {
		const showSaveFiltersDialog = ref(false);
		const renderOptions = computed(() => {
			const options = {
				fields: {},
				base: props.options.base || "12",
				filterBox: props.options.filterBox || false,
				presetFilters: props.options.presetFilters || false,
			};
			for (let i in props.options.fields) {
				options.fields[i] = {
					label: props.options.fields[i].label || i,
					width: props.options.fields[i].width || 1,
					priority: props.options.fields[i].priority || 5,
					align: props.options.fields[i].align || "left",
				};
			}
			return options;
		});
		provide("renderOptions", renderOptions);
		return {
			showSaveFiltersDialog,
			renderOptions,
		};
	},
	computed: {
		isLoading() {
			return this.manager.loading;
		},
	},
	methods: {
		sortArrowShow(field) {
			const [orderByField] = this.manager.options.order_by.split(" ");
			return orderByField === field;
		},
		sortArrowName() {
			const [_, sortOrder] = this.manager.options.order_by.split(" ");
			return sortOrder === "desc" ? "chevron-up" : "chevron-down";
		},
	},
};
</script>
