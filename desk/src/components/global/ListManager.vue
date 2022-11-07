<template>
	<div class="h-full">
		<slot name="body" :manager="manager" />
	</div>
</template>

<script>
import { ref, computed, watch, provide } from "vue"

export default {
	name: "ListManager",
	props: ["options"],
	setup(props, context) {
		const options = ref({
			handle_row_click: () => {},
			...props.options,
		})

		options.value.fields = [
			...new Set([...(options.value.fields || []), "name"]),
		]

		const resources = ref(null)
		const selectedItems = ref({})
		const selectionMode = ref(0)

		const allItemsSelected = computed(() => {
			if (manager.value.loading) {
				return false
			} else {
				if (manager.value.list.length > 0) {
					return (
						Object.keys(selectedItems.value).length ==
						manager.value.list.length
					)
				}
				return false
			}
		})
		const manager = ref({
			loading: false,
			resources,
			options,
			selectedItems,
			allItemsSelected,
			list: [],
			totalCount: 0,
			nextPage: () => {
				resources.value.list.next()
			},
			hasNextPage: computed(() => {
				return resources?.value?.list?.hasNextPage
			}),
			reload: () => {
				clearList()
				resources.value.list.reload()
			},
			update: (newOptions) => {
				clearList()
				if (newOptions.filters)
					options.value.filters = newOptions.filters
				if (newOptions.order_by)
					options.value.order_by = newOptions.order_by

				resources.value.list.update(options.value)
			},
			itemSelected: (rowData) => {
				return rowData.name in selectedItems.value
			},
			onClick: (rowData) => {
				if (selectionMode.value == 1) {
					selectionMode.value = 2
				} else if (selectionMode.value == 2) {
					manager.value.select(rowData)
				} else {
					options.value.handle_row_click(rowData)
				}
			},
			unselect: () => {
				selectedItems.value = {}
			},
			selectAll: () => {
				if (allItemsSelected.value) {
					manager.value.unselect()
				} else {
					for (let i = 0; i < manager.value.list.length; i++) {
						selectedItems.value[manager.value.list[i].name] =
							manager.value.list[i]
					}
				}
				context.emit("selection", selectedItems.value)
			},
			select: (rowData) => {
				if (selectionMode.value == 0) {
					selectionMode.value = 1
				}
				if (rowData.name in selectedItems.value) {
					delete selectedItems.value[rowData.name]
					if (Object.keys(selectedItems.value).length == 0) {
						selectionMode.value = 0
					}
				} else {
					selectedItems.value[rowData.name] = rowData
				}
			},
			toggleOrderBy: (field) => {
				let newOrderBy = `${field} desc`
				const oldOrderBy = options.value?.order_by
				if (oldOrderBy) {
					if (oldOrderBy.split(" ")[0] === newOrderBy.split(" ")[0]) {
						newOrderBy = `${field} ${
							oldOrderBy.split(" ")[1] === "desc" ? "asc" : "desc"
						}`
					}
				}
				manager.value.update({ order_by: newOrderBy })
			},
		})
		provide("manager", manager)

		const clearList = () => {
			selectedItems.value = {}
		}

		manager.value.list = computed(() => {
			manager.value?.resources?.count.fetch({
				doctype: manager.value.options.doctype,
				filters: manager.value.options.filters,
			})
			return manager.value?.resources?.list?.data || []
		})

		manager.value.loading = computed(() => {
			return manager.value.resources?.list?.list.loading
		})

		watch(selectedItems.value, (newValue) => {
			context.emit("selection", newValue)
		})

		return {
			manager,
			selectedItems,
			selectionMode,
			clearList,
		}
	},
	mounted() {
		this.manager.resources = this.$resources
	},
	unmounted() {
		this.cleanup()
	},
	resources: {
		list() {
			return {
				type: "list",
				doctype: this.manager.options?.doctype,
				fields: this.manager.options?.fields,
				cache: this.manager.options?.cache,
				order_by: this.manager.options?.order_by,
				filters: this.manager.options?.filters,
				limit: this.manager.options?.limit || 20,
				realtime: true,
			}
		},
		count() {
			return {
				method: "frappe.client.get_count",
				onSuccess: (count) => {
					this.manager.totalCount = count
					this.manager.totalPages = Math.ceil(
						count / this.options.limit
					)
				},
			}
		},
	},
	methods: {
		cleanup() {
			this.$socket.off("list_update")
		},
	},
}
</script>
