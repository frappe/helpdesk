<template>
	<div class="h-full">
		<slot name="body" :manager="manager" />
	</div>
</template>

<script>
import { ref, computed, watch, provide, inject, nextTick } from "vue"
import { useRouter } from "vue-router"
import { createListResource, createResource } from "frappe-ui"
import { onMounted } from "@vue/runtime-core"

export default {
	name: "ListManager",
	props: ["options"],
	setup(props, context) {
		const router = useRouter()
		const user = inject("user")

		const options = ref({
			handleRowClick: () => {},
			cache: props.options.cache || null,
			fields: [...new Set([...(props.options.fields || []), "name"])],
			doctype: props.options.doctype,
			filters: props.options.filters || [],
			limit: props.options.limit || 20,
			order_by: props.options.order_by || "",
		})

		const listResource = createListResource(
			{
				type: "list",
				cache: options.value.cache,
				doctype: options.value.doctype,
				fields: options.value.fields,
				order_by: options.value.order_by,
				filters: options.value.filters,
				limit: options.value.limit,
				realtime: true,
			},
			context
		)
		const list = computed(() => {
			countResource.fetch({
				doctype: options.value.doctype,
				filters: options.value.filters,
			})
			return listResource.list.data || []
		})
		const loading = computed(() => {
			return listResource.list.loading
		})

		const countResource = createResource(
			{
				method: "frappe.client.get_count",
			},
			context
		)
		const totalCount = computed(() => {
			return countResource.data || 0
		})

		const reload = () => {
			selectedItems.value = {}
			listResource.reload()
		}
		const update = (newOptions) => {
			if (newOptions.filters) options.value.filters = newOptions.filters
			if (newOptions.order_by)
				options.value.order_by = newOptions.order_by

			listResource.update({
				...options.value,
			})
		}

		const nextPage = () => {
			listResource.next()
		}
		const hasNextPage = computed(() => {
			return listResource.hasNextPage
		})

		const sudoFilters = ref([])
		const generateExecutableFilter = (filter) => {
			let mapOperator = (x) => {
				switch (x) {
					case "is":
						return "="
					case "is not":
						return "!="
					case "before":
						return "<"
					case "after":
						return ">"
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
				filterType = filter.filter_type == "is" ? "like" : "not like"
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
		}
		const addFilters = (sudoFilters, addToUrlQuery) => {
			if (addToUrlQuery) {
				let query = {}
				sudoFilters.forEach((filter) => {
					let fieldname = filter.fieldname
					let filter_type = filter.filter_type
					let value =
						filter.fieldname == "_assign" && filter.value == "@me"
							? user.value.user
							: filter.value

					query[fieldname] = JSON.stringify([filter_type, value])
				})
				// adding to the route will trigger the route(watcher) to apply filters
				router.replace({ query })
			} else {
				let executableFilters = []
				for (let i in sudoFilters) {
					executableFilters.push(
						generateExecutableFilter(sudoFilters[i])
					)
				}
				applyFilters(executableFilters)
			}
		}
		const applyFilters = (executableFilters) => {
			manager.value.update({
				filters: executableFilters,
			})
		}

		const toggleOrderBy = (field) => {
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
		}

		const onClick = (rowData) => {
			if (selectionMode.value == 1) {
				selectionMode.value = 2
			} else if (selectionMode.value == 2) {
				manager.value.select(rowData)
			} else {
				options.value.handleRowClick(rowData)
			}
		}

		const select = (rowData) => {
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
		}
		const unselect = () => {
			selectedItems.value = {}
		}
		const selectAll = () => {
			if (allItemsSelected.value) {
				manager.value.unselect()
			} else {
				for (let i = 0; i < manager.value.list.length; i++) {
					selectedItems.value[manager.value.list[i].name] =
						manager.value.list[i]
				}
			}
			context.emit("selection", selectedItems.value)
		}

		const selectionMode = ref(0)
		const selectedItems = ref({})
		watch(selectedItems.value, (newValue) => {
			context.emit("selection", newValue)
		})
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
		const itemSelected = (rowData) => {
			return rowData.name in selectedItems.value
		}

		const manager = ref({
			options,

			list,
			loading,
			totalCount,

			reload,
			update,

			nextPage,
			hasNextPage,

			sudoFilters,
			addFilters,

			toggleOrderBy,

			onClick,

			select,
			unselect,
			selectAll,

			selectionMode,
			selectedItems,
			allItemsSelected,
			itemSelected,
		})
		provide("manager", manager)

		onMounted(() => {
			nextTick(() => {
				reload()
			})
		})
	},
}
</script>
