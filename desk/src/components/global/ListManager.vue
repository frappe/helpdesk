<template>
	<div class="h-full">
		<slot name="body" :manager="manager" />
	</div>
</template>

<script>
import { ref, computed, watch, provide, inject } from "vue"

export default {
	name: "ListManager",
	props: ["options"],
	setup(props, context) {
		const user = inject("user")
		const options = ref({
			handle_row_click: () => {},
			fields: props.options.fields || [],
			doctype: props.options.doctype,
			filters: props.options.filters || [],
			limit: props.options.limit || 20,
			order_by: props.options.order_by || "",
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
			generateExecutableFilter: (filter) => {
				let mapOperator = (x) => {
					switch (x) {
						case "is":
							return "="
						case "is not":
							return "!="
						default:
							return x
					}
				}
				let mapValue = (x, type) => {
					switch (type) {
						case "like":
							return `%${x}%`
						case "not like":
							return `%${x}%`
						default:
							return x
					}
				}

				let filterType = filter.filter_type
				if (filter.fieldname == "_assign") {
					filterType =
						filter.filter_type == "is" ? "like" : "not like"
				}

				let executableFilter = [
					filter.fieldname,
					mapOperator(filterType),
					mapValue(
						filter.fieldname == "_assign" && filter.value == "@me"
							? user.value.user
							: filter.value,
						filterType
					),
				]
				return executableFilter
			},
			addFilter: (filter, append = true) => {
				let executableFilter =
					manager.value.generateExecutableFilter(filter)
				manager.value.applyFilters([filter], [executableFilter], append)
			},
			addFilters: (filters, append = true) => {
				let executableFilters = []
				for (let i in filters) {
					executableFilters.push(
						manager.value.generateExecutableFilter(filters[i])
					)
				}
				manager.value.applyFilters(filters, executableFilters, append)
			},
			applyFilters: (filters, executableFilters, append = true) => {
				// applyFilters should be called with a list of executable filters only
				let finaleExecutableFilters = []
				if (append) {
					finaleExecutableFilters = [
						...manager.value.options.filters,
						...executableFilters,
					]
				} else {
					finaleExecutableFilters = executableFilters
				}
				manager.value.update({
					filters: finaleExecutableFilters,
				})
			},
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
				cache: this.manager.options?.cache,
				doctype: this.manager.options.doctype,
				fields: this.manager.options.fields,
				order_by: this.manager.options.order_by,
				filters: this.manager.options.filters,
				limit: this.manager.options.limit,
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
