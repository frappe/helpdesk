<template>
  <div>
    <slot name="body" :manager="manager"/>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'ListManager',
  props: ['options'],
  setup(props) {
    const options = {
      handle_row_click: () => {},
      ...props.options
    }
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
      start: 0,
      currPage: 1,
      totalPages: 0,
      previousPage: () => {
        if (manager.value.start > 0) {
          let newStart = manager.value.start - options.limit
          if (newStart < 0) {
            newStart = 0
          }
          manager.value.loadPage(newStart)
        }
      },
      nextPage: () => {
        manager.value.loadPage(manager.value.start + options.limit)
      },
      getPage: (page) => {
        manager.value.loadPage(options.limit * (page - 1))
      },
      loadPage: (start) => {
        clearList()
        manager.value.start = start
        manager.value.currPage = Math.floor(manager.value.start / options.limit) + 1
        resources.value.list.update({
          ...options,
          start: manager.value.start,
          limit: options.limit
        })
      },
      hasPage: (page) => {
        if (page <= 0) return false
        return page <= manager.value.totalPages
      },
      reload: () => {
        manager.value.currPage = 1
        resources.value.list.update({
          ...options,
          start: 0,
          limit: options.limit
        })
      },
      update: (newOptions) => {
        clearList()
        manager.value.currPage = 1
        if (newOptions.filters) options.filters = newOptions.filters
        if (newOptions.order_by) options.order_by = newOptions.order_by
        resources.value.list.update({
          ...options,
          start: 0,
          limit: options.limit
        })
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
          manager.value.options.handle_row_click(rowData)
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
        const oldOrderBy = manager.value.options?.order_by
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
      selectionMode
    }
  },
  mounted() {
    this.manager.resources = this.$resources
    this.handleRealtimeUpdate()
  },
  unmounted() {
    this.cleanup()
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
        start: 0,
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
          this.manager.totalPages = Math.ceil(count / this.manager.options.limit)
        }
      }
    }
  },
  methods: {
    handleRealtimeUpdate() {
      this.$socket.on("list_update", (data) => {
        if (data.doctype === this.options.doctype) {
          this.$resources.document.fetch({
            doctype: this.manager.options.doctype,
            filters: {
              ...this.options.filters,
              name: data.name
            },
            fields: this.manager.options.fields,
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