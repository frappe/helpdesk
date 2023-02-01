<template>
	<div class="h-full">
		<slot name="body" :manager="manager" />
	</div>
</template>

<script>
import { ref, computed, watch, provide, inject, nextTick } from "vue"
import { useRouter, useRoute } from "vue-router"
import { createListResource, createResource } from "frappe-ui"
import { onMounted } from "@vue/runtime-core"

export default {
	name: "ListManager",
	props: ["options"],
	setup(props, context) {
		const router = useRouter()
		const route = useRoute()

		const user = inject("user")

		const options = ref({
			handleRowClick: () => {},
			urlQueryFilters: props.options.urlQueryFilters || false,
			saveFiltersLocally: props.options.saveFiltersLocally || false,
			cache: props.options.cache || null,
			fields: [...new Set([...(props.options.fields || []), "name"])],
			doctype: props.options.doctype,
			filters: props.options.filters || [],
			limit: props.options.limit || 20,
			start: 0,
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
				start: options.value.start,
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

		const idWidth = computed(() => {
			// Default width for id column in cases where calculation is impossible
			const defaultWidth = 1;

			// Minimum length of id. This is an assumed value, and could be wrong
			const minIdLength = 3;

			// Spread operator is used to clone original array
			const data = [...(listResource.data || [])];

			// Find row with longest id from data.
			const longest = data
				.sort((a, b) => a.name.length - b.name.length)
				.pop();

			// Default width if longest name is not found. This could happen in
			// case of an empty list
			if (!longest) return defaultWidth;

			// Length is the length of name string. `name` here the key and should not
			// be confused with other properties like subject
			const idLength = longest.name.length;

			// Default width is enough for short ids
			if (idLength <= minIdLength) return defaultWidth;

			// Reduce minimum width, to adjust width according to remaining width
			const extraWidth = idLength - minIdLength;

			// This value will be passed to tailwind width classes, which does not
			// support fractional values. (It does support some, but not all).
			// Refer https://tailwindcss.com/docs/width for more
			//
			// Extra width is here is the number of characters and we don't need that
			// number in pixels/css. Hence the it is divided by another number. This
			// could be a flaw and improved if possible
			return Math.ceil(extraWidth / 3);
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
		const fetch = () => {
			listResource.list.fetch()
		}
		const update = (newOptions = null) => {
			if (newOptions) {
				if (newOptions.filters)
					options.value.filters = newOptions.filters
				if (newOptions.order_by)
					options.value.order_by = newOptions.order_by
			}

			listResource.update({
				...options.value,
			})
		}

		const getPage = (page) => {
			if (page < 0 || page > totalPages.value) return
			options.value.start = (page - 1) * options.value.limit
			update()
			fetch()
		}
		const nextPage = () => {
			if (currentPageNumber.value == totalPages.value) return
			options.value.start += options.value.limit
			update()
			fetch()
		}
		const previousPage = () => {
			if (currentPageNumber.value == 1) return
			let newStart = options.value.start - options.value.limit
			if (newStart < 0) newStart = 0
			options.value.start = newStart
			update()
			fetch()
		}
		const hasNextPage = computed(() => {
			return options.value.start + options.value.limit < totalCount.value
		})
		const hasPreviousPage = computed(() => {
			return options.value.start > 0
		})
		const currentPageNumber = computed(() => {
			return Math.ceil(options.value.start / options.value.limit) + 1
		})
		const totalPages = computed(() => {
			return Math.ceil(totalCount.value / options.value.limit)
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
				router.replace({ query })
				if (
					Object.keys(query).length == 0 &&
					options.value.saveFiltersLocally
				) {
					applyFilters()
				}
			} else {
				let executableFilters = []
				for (let i in sudoFilters) {
					executableFilters.push(
						generateExecutableFilter(sudoFilters[i])
					)
				}
				applyFilters(sudoFilters, executableFilters)
			}
		}
		const applyFilters = (sudoFilters = [], executableFilters = []) => {
			if (options.value.saveFiltersLocally) {
				localStorage.setItem(
					`list_filters_${route.path}`,
					JSON.stringify(sudoFilters || [])
				)
			}
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
			update({ order_by: newOrderBy })
			reload()
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

		const convertFieldNameToLabel = (fieldname) => {
			switch (fieldname) {
				case "_assign":
					return "Assigned to"
				case "_seen":
					return false
				default:
					fieldname = fieldname.replace(/_/g, " ")
					return (
						fieldname.charAt(0).toUpperCase() + fieldname.slice(1)
					)
			}
		}
		const convertUrlQueryToFilters = () => {
			let urlQuery = route.query
			let filters = []

			for (let key in urlQuery) {
				let filterType = "like"
				let value = ""
				urlQuery[key] = JSON.parse(urlQuery[key])
				if (urlQuery[key].constructor.name == "Array") {
					if (urlQuery[key].length == 1) {
						value = urlQuery[key][0]
					} else {
						filterType = urlQuery[key][0]
						value = urlQuery[key][1]
					}
				} else {
					value = urlQuery[key]
				}
				let filter = {
					label: convertFieldNameToLabel(key),
					fieldname: key,
					filter_type: filterType,
					value,
				}
				filters.push(filter)
			}
			return filters
		}

		const manager = ref({
			options,

			list,
			loading,
			totalCount,
			idWidth,

			reload,
			update,

			getPage,
			nextPage,
			previousPage,
			hasNextPage,
			hasPreviousPage,
			currentPageNumber,
			totalPages,

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

			helperMethods: {
				convertFieldNameToLabel,
			},
		})
		provide("manager", manager)

		onMounted(() => {
			nextTick(() => {
				if (
					options.value.urlQueryFilters &&
					Object.keys(route.query).length > 0
				) {
					sudoFilters.value = convertUrlQueryToFilters()
					addFilters(sudoFilters.value, false)
				} else if (options.value.saveFiltersLocally) {
					sudoFilters.value = JSON.parse(
						localStorage.getItem(`list_filters_${route.path}`) ||
							"[]"
					)
					addFilters(sudoFilters.value, options.value.urlQueryFilters)
				}
				reload()
			})
		})

		return {
			manager,
		}
	},
}
</script>
