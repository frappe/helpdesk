<template>
	<div class="h-full">
		<div
			v-if="false"
			class="w-1/12 w-2/12 w-3/12 w-4/12 w-5/12 w-6/12 w-7/12 w-8/12 w-9/12 w-10/12 w-11/12"
		></div>
		<slot name="body">
			<slot v-if="!manager.loading" name="list-body">
				<div>
					<slot name="top-section">
						<div
							class="flex flex-row w-full items-center h-[30px] mb-4 space-x-2"
						>
							<div>
								<slot name="top-sub-section-1">
									<!-- Filter Box -->
								</slot>
							</div>
							<div class="grow">
								<slot name="top-sub-section-2">
									<!-- Filter Box -->
									<div class="flex flex-row items-center">
										<Button
											icon-right="chevron-down"
											class="mr-[-10px] bg-gray-300"
											>Filters</Button
										>
										<div class="grow">
											<Input
												type="text"
												class="h-[30px]"
											></Input>
										</div>
									</div>
								</slot>
							</div>
							<div>
								<slot name="top-sub-section-3">
									<div
										v-if="
											Object.keys(manager.selectedItems)
												.length > 0
										"
									>
										<slot
											name="bulk-actions"
											:selectedItems="
												manager.selectedItems
											"
										>
											<!-- Bulk Actions -->
										</slot>
									</div>
									<div v-else class="flex flex-row space-x-2">
										<div>
											<slot name="actions">
												<!-- Actions -->
											</slot>
										</div>
										<div>
											<slot name="primary-action">
												<!-- Add Item -->
												<Button
													appearance="primary"
													icon-left="plus"
												>
													{{
														`Add ${manager.options.doctype}`
													}}
												</Button>
											</slot>
										</div>
									</div>
									<!-- Actions / Bulk actions -->
								</slot>
							</div>
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
									:class="`w-${renderOptions.fields[field].width}/12`"
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
					<slot name="rows" :items="manager.list">
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
											:class="`w-${renderOptions.fields[field].width}/12`"
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
				</div>
			</slot>
			<slot v-else name="listLoading"> List is loading... </slot>
		</slot>
	</div>
</template>

<script>
import ListManager from "./ListManager.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "ListViewer",
	props: {
		manager: {
			type: Object,
			required: true,
		},
		options: {
			type: Object,
			default: () => ({}),
		},
	},
	components: {
		ListManager,
		CustomIcons,
	},
	computed: {
		renderOptions() {
			const options = { fields: {} }
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
}
</script>
