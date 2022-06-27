<template>
  <div>
    <slot name="body" :manager="manager"/>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'ListManager',
  props: ['options'],
  setup(props) {
    const router = useRouter()
    const route = useRoute()

    const options = ref({
      handle_row_click: () => {},
      ...props.options
    })
    const resources = ref(null)
    const newItems = ref([])
    const selectedItems = ref({})
    const selectionMode = ref(0)

    const allItemsSelected = computed(() => {
      if (manager.value.loading) {
        return false
      } else {
        if (manager.value.list.length > 0) {
          return Object.keys(selectedItems.value).length == manager.value.list.length
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
      start: options.value.limit * (options.value.start_page - 1),
      currPage: options.value.start_page || 1,
      totalPages: 0,
      previousPage: () => {
        if (manager.value.start > 0) {
          let newStart = manager.value.start - options.value.limit
          if (newStart < 0) {
            newStart = 0
          }
          manager.value.loadPage(newStart)
        }
      },
      nextPage: () => {
        manager.value.loadPage(manager.value.start + options.value.limit)
      },
      getPage: (page) => {
        manager.value.loadPage(options.value.limit * (page - 1))
      },
      loadPage: (start) => {
        if (options.value.route_query_pagination && manager.value.start != start) {
          router.push({
            query: {...route.query, page: Math.ceil(start / options.value.limit) + 1}
          })
        } else {
          clearList()
          manager.value.currPage = Math.floor(manager.value.start / options.value.limit) + 1
          resources.value.list.update({
            ...options.value,
            start: manager.value.start,
            limit: options.value.limit
          })
        }
      }, 
      hasPage: (page) => {
        if (page <= 0) return false
        return page <= manager.value.totalPages
      },
      reload: () => {
        manager.value.currPage = 1
        if (options.value.route_query_pagination) {
          router.push({
            query: {...route.query, page: 1}
          })
        } else {
          resources.value.list.update({
            ...options.value,
            start: 0,
            limit: options.value.limit
          })
        }
      },
      update: (newOptions) => {
        clearList()
        if (newOptions.filters) options.value.filters = newOptions.filters
        if (newOptions.order_by) options.value.order_by = newOptions.order_by

        manager.value.currPage = parseInt(route.query.page ? route.query.page : 1)
        manager.value.getPage(manager.value.currPage)
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
      selectAll: () => {
        if (allItemsSelected.value) {
          selectedItems.value = {}
        } else {
          for (let i = 0; i < manager.value.list.length; i++) {
            selectedItems.value[manager.value.list[i].name] = manager.value.list[i]
          }
        }
      },
      select: (rowData) => {
        if (selectionMode.value == 0) {
          selectionMode.value = 1
        }
        if(rowData.name in selectedItems.value) {
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
          if (oldOrderBy.split(' ')[0] === newOrderBy.split(' ')[0]) {
            newOrderBy = `${field} ${oldOrderBy.split(' ')[1] === 'desc' ? 'asc' : 'desc'}`
          }
        }
        manager.value.update({order_by: newOrderBy})
      }
    })

    const clearList = () => {
      newItems.value = []
      selectedItems.value = {}
    }

    manager.value.list = computed(() => {
      manager.value?.resources?.count.fetch({
        doctype: manager.value.options.doctype,
        filters: manager.value.options.filters
      })
      return manager.value?.resources?.list?.data || []
    })

    manager.value.loading = computed(() => {
      return manager.value.resources?.list?.list.loading
    })

    return {
      manager,
      newItems,
      selectedItems,
      selectionMode,
      clearList
    }
  },
  mounted() {
    this.manager.resources = this.$resources
    this.handleRealtimeUpdate()
  },
  unmounted() {
    this.cleanup()
  },
  watch: {
    $route() {
      this.syncPage()
    }
  },
  resources: {
    list() {
      return {
        type: 'list',
        doctype: this.options?.doctype,
        fields: [...this.options?.fields, "name"],
        cache: this.options?.cache,
        order_by: this.options?.order_by,
        filters: this.options?.filters,
        start: this.options?.limit * (this.options?.start_page - 1),
        limit: this.options?.limit || 20,
        onSuccess: (data) => {
          /**
           * Remove all the duplicates which might have been added to the
           * current list when new entry was added via socket list_update
           */
          var newItems = this.newItems
          data = data.filter(function(i) {
            return !newItems.find(j => {
              return j === i.name
            });
          });
        }
      }
    },
    document() {
      return {
        method: 'frappe.client.get_list',
        onSuccess: (data) => {
          if (data.length > 0) {
            const itemIndex = this.manager.list.findIndex(item => item.name === data[0].name)
            if (itemIndex != -1) {
              this.manager.list[itemIndex] = data[0]
            } else {
              this.manager.list.unshift(data[0])
              this.newItems.push(data[0].name)
            }
          }
        }
      }
    },
    count() {
      return {
        method: 'frappe.client.get_count',
        onSuccess: (count) => {
          this.manager.totalPages = Math.ceil(count / this.options.limit)
        }
      }
    }
  },
  methods: {
    syncPage() {
      if (!this.options.route_query_pagination) return
      if (this.$route.query.page) {
        let page = this.$route.query.page
        if (page <= 0) {
          return this.$router.push({
            query: {...this.$route.query, page: 1}
          })
        }
        const start = this.options.limit * (page - 1)

        this.clearList()
        this.manager.start = start
        this.manager.currPage = Math.floor(this.manager.start / this.options.limit) + 1
        this.$resources.list.update({
          ...this.manager.options,
          start: this.manager.start,
          limit: this.options.limit
        })
      }
    },
    handleRealtimeUpdate() {
      this.$socket.on("list_update", (data) => {
        if (data.doctype === this.options.doctype) {
          this.$resources.document.fetch({
            doctype: this.options.doctype,
            filters: {
              ...this.options.filters,
              name: data.name
            },
            fields: this.options.fields,
            limit: 1
          })
        }
      })
    },
    cleanup() {
      this.$socket.off("list_update")
    }
  }
}
</script>