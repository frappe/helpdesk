<template>
	<div class="h-full">
		<div
			v-if="false"
			class="w-1/12 w-2/12 w-3/12 w-4/12 w-5/12 w-6/12 w-7/12 w-8/12 w-9/12 w-10/12 w-11/12"
		></div>
		<div
			v-if="false"
			class="w-1/24 w-2/24 w-3/24 w-4/24 w-5/24 w-6/24 w-7/24 w-8/24 w-9/24 w-10/24 w-11/24 w-12/24 w-13/24 w-14/24 w-15/24 w-16/24 w-17/24 w-18/24 w-19/24 w-20/24 w-21/24 w-22/24 w-23/24"
		></div>
		<slot name="body">
			<slot name="list-body">
				<div>
					<slot name="top-section">
						<div
							class="flex flex-row w-full items-center h-[30px] mb-4 space-x-2"
						>
							<slot name="top-sub-section-1">
								<PresetFilters
									v-if="options.presetFilters"
									@apply-filter="applyFilter"
								/>
							</slot>
							<div class="grow">
								<slot name="top-sub-section-2">
									<!-- Filter Box -->
									<div
										v-if="options.filterBox"
										class="flex flex-row items-center space-x-1"
									>
										<div
											class="py-1 px-2 bg-white rounded shadow flex flex-row space-x-1 items-center"
										>
											<div class="text-base">
												assignee:
												<span class="font-semibold"
													>@me</span
												>
											</div>
											<button
												class="grid w-4 h-4 text-gray-700 rounded hover:bg-gray-300 place-items-center"
											>
												<FeatherIcon
													class="w-3"
													name="x"
												/>
											</button>
										</div>
										<div
											class="py-1 px-2 bg-white rounded shadow flex flex-row space-x-1 items-center"
										>
											<div class="text-base">
												status:
												<span class="font-semibold"
													>Open</span
												>
											</div>
											<button
												class="grid w-4 h-4 text-gray-700 rounded hover:bg-gray-300 place-items-center"
											>
												<FeatherIcon
													class="w-3"
													name="x"
												/>
											</button>
										</div>
										<FeatherIcon
											name="plus"
											class="h-3 w-3"
										/>
									</div>
								</slot>
							</div>
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
										:selectedItems="manager.selectedItems"
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
												`Add ${manager.options.doctype}`
											}}
										</Button>
									</slot>
								</div>
							</slot>
						</div>
					</slot>
					<slot name="header">
						<div class="w-full">
							<div
								class="flex flex-row bg-[#F7F7F7] group items-center text-base font-medium text-gray-500 py-[10px] p-[10px] rounded-[6px] select-none"
							>
								<div class="w-[25px]">
									<Input
										type="checkbox"
										@click="manager.selectAll()"
										:checked="manager.allItemsSelected"
										class="cursor-pointer mr-1"
									/>
								</div>
								<div
									v-for="field in Object.keys(
										renderOptions.fields
									)"
									:key="field"
									:class="`w-${renderOptions.fields[field].width}/${renderOptions.base}`"
								>
									<div>
										<slot
											:name="'header-field-' + field"
											:field="field"
										>
											<div
												class="flex space-x-1 items-center"
												:class="
													renderOptions.fields[field]
														.align === 'right'
														? 'flex-row-reverse'
														: 'flex-row'
												"
											>
												<div
													class="hover:text-gray-600 cursor-pointer fill-gray-400"
													:class="
														renderOptions.fields[
															field
														].align === 'right'
															? 'ml-1'
															: ''
													"
													@click="
														manager.toggleOrderBy(
															field
														)
													"
												>
													{{
														renderOptions.fields[
															field
														].label
													}}
												</div>
												<div class="w-[10px]">
													<CustomIcons
														v-if="
															manager.options.order_by.split(
																' '
															)[0] === field
														"
														:name="
															manager.options.order_by.split(
																' '
															)[1] === 'desc'
																? 'chevron-down'
																: 'chevron-up'
														"
														class="h-[6px] fill-gray-400 stroke-transparent"
													/>
												</div>
											</div>
										</slot>
									</div>
								</div>
							</div>
						</div>
					</slot>
					<slot
						v-if="!manager.loading"
						name="rows"
						:items="manager.list"
					>
						<div class="flex flex-col w-full">
							<div
								v-for="(item, index) in manager.list"
								:key="item.name"
							>
								<slot name="row" :item="item">
									<div
										class="flex flex-row items-center px-[10px] select-none rounded-[6px] py-[9px]"
										:class="`${
											manager.itemSelected(item)
												? 'bg-blue-50 hover:bg-blue-100'
												: 'hover:bg-gray-50'
										} ${
											index == 0
												? 'mt-[9px] mb-[2px]'
												: 'my-[2px]'
										}`"
									>
										<div class="w-[25px]">
											<Input
												type="checkbox"
												@click="manager.select(item)"
												:checked="
													manager.itemSelected(item)
												"
												class="cursor-pointer"
											/>
										</div>
										<div
											v-for="field in Object.keys(
												renderOptions.fields
											)"
											:key="field"
											:class="`w-${renderOptions.fields[field].width}/${renderOptions.base}`"
										>
											<div
												class="flex"
												:class="
													renderOptions.fields[field]
														.align === 'right'
														? 'justify-end'
														: 'justify-start line-clamp-1'
												"
											>
												<slot
													:name="'field-' + field"
													:field="field"
													:value="item[field]"
													:row="item"
												>
													<div>
														{{ item[field] }}
													</div>
												</slot>
											</div>
										</div>
									</div>
								</slot>
							</div>
						</div>
					</slot>
					<slot v-else name="listLoading"> List is loading... </slot>
				</div>
			</slot>
		</slot>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import PresetFilters from "@/components/global/PresetFilters.vue"
import { Dropdown, FeatherIcon } from "frappe-ui"

export default {
	name: "ListViewer",
	props: {
		options: {
			type: Object,
			default: () => ({}),
		},
	},
	inject: ["manager"],
	components: {
		CustomIcons,
		PresetFilters,
		Dropdown,
		FeatherIcon,
	},
	computed: {
		renderOptions() {
			const options = {
				fields: {},
				base: this.options.base || "12",
				filterBox: this.options.filterBox || false,
				presetFilters: this.options.presetFilters || false,
			}
			for (let i in this.options.fields) {
				options.fields[i] = {
					label: this.options.fields[i].label || i,
					width: this.options.fields[i].width || 1,
					priority: this.options.fields[i].priority || 5,
					align: this.options.fields[i].align || "left",
				}
			}
			return options
		},
	},
	methods: {
		applyFilter(filters) {
			this.manager.applyFilters(filters)
		},
	},
}
</script>
