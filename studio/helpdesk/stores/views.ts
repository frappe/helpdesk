import { computed, nextTick, ref, shallowRef, toRaw, watch } from 'vue'
import { StorageSerializers, useStorage } from '@vueuse/core'
import { call, createListResource, toast } from 'frappe-ui'
import { parseOrderBy } from '@framework/ui/SortBy'
import { parseColumns } from '@framework/ui/ColumnSettings'
import { normalizeFilters, toConditions } from '@helpdesk/shared/filter'
import { __ } from '@helpdesk/shared/translation'
import { currentRoute, navigateTo } from '@app/stores/router'
import { useSession } from '@app/stores/session'
import { askConfirm, parseJson, runAction, setValues } from '@helpdesk/shared/utils'

const DOCTYPE = 'HD Ticket'

const DEFAULT_VIEW = { name: '', icon: 'text-align-justify' }

// Storage, not the URL: every way back into this list pushes a bare route.
const MEMORY_PREFIX = 'kb:list'

const store = createViewsStore()

export function useViews(listView) {
  store.attachListView(listView)
  return store.bindings
}

function sessionUser() {
  return useSession().config.value?.session_user || ''
}

function createViewsStore() {
  const list = createListResource({
    doctype: 'HD View',
    fields: [
      'name', 'label', 'icon', 'dt', 'route_name', 'pinned', 'public',
      'is_default', 'is_standard', 'filters', 'order_by', 'columns', 'user',
    ],
    // `is_default` rows are the old portal's auto-saved list state, never a named view.
    filters: { dt: DOCTYPE, is_customer_portal: 1, is_default: 0 },
    pageLength: 1000,
  })

  const views = computed(() => list.data || [])

  const listView = shallowRef(null)
  let hasAttached = false
  const defaultSnapshot = shallowRef(null)
  let isRestoring = false

  const isViewModalOpen = ref(false)
  const viewModalMode = ref<'create' | 'rename'>('create')
  const viewModalLabel = ref('')
  const viewModalIcon = ref('')
  const viewModalName = ref('')

  const activeName = computed(() => currentRoute().query?.view || '')

  const activeView = computed(
    () => views.value.find((view) => view.name === activeName.value) || null,
  )

  // No saved columns means the default List columns, as the old portal stored them.
  const activeLayout = computed(() => {
    const row = activeView.value
    if (!row) return null
    const columns = parseViewColumns(row.columns)
    return {
      filters: parseViewFilters(row.filters),
      sort: parseOrderBy(row.order_by || ''),
      columns: columns.length ? columns : defaultSnapshot.value?.columns,
    }
  })

  const currentView = computed(() =>
    activeView.value
      ? { ...activeView.value, icon: activeView.value.icon || DEFAULT_VIEW.icon }
      : { ...DEFAULT_VIEW, label: __('List') },
  )

  // Per user: another customer on this browser would get these filters.
  const memoryKey = (name) => `${MEMORY_PREFIX}:${sessionUser()}:${DOCTYPE}:${name}`
  const rememberedLayout = useStorage(
    () => memoryKey(activeName.value),
    null,
    localStorage,
    { serializer: StorageSerializers.object, writeDefaults: false },
  )

  // Not in attachListView: Studio stops the page's effect scope on navigation.
  watch(() => [activeName.value, list.data], () => applyActiveView())
  watch(
    () =>
      listView.value && [
        listView.value.filters.conditions.value,
        listView.value.sort.by.value,
        listView.value.columns.shown.value,
      ],
    () => rememberLayout(),
    { deep: true },
  )

  function attachListView(view) {
    // Before any restore: the defaults for "List" and for views with no saved columns.
    defaultSnapshot.value ??= snapshotOf(view)
    // The store outlives the page: rebind on every mount.
    listView.value = view
    // The watch fires on neither a same-view return nor a remount.
    applyActiveView()
    if (hasAttached) return
    hasAttached = true
    // `if_owner` does not cover agents.
    useSession()
      .loadSession()
      .then(() => {
        list.update({ filters: { ...list.filters, owner: sessionUser() } })
        return list.reload()
      })
  }

  function rememberLayout() {
    const view = listView.value
    // Until the views load, a requested view shows the defaults, not that view.
    if (isRestoring || !view || !sessionUser() || (activeName.value && !list.data)) return
    rememberedLayout.value = {
      filters: view.filters.conditions.value,
      sort: view.sort.by.value,
      columns: view.columns.shown.value,
    }
  }

  function applyActiveView() {
    const view = listView.value
    if (!view) return
    isRestoring = true
    const layout = activeLayout.value || defaultSnapshot.value
    if (layout) view.restore(structuredClone(layout))
    // An empty remembered sort was never chosen.
    const remembered = rememberedLayout.value
    if (remembered) {
      view.restore({
        filters: remembered.filters,
        ...(remembered.sort?.length ? { sort: remembered.sort } : {}),
        ...(remembered.columns?.length ? { columns: remembered.columns } : {}),
      })
    }
    // Next tick, so the restore's own writes are not remembered.
    nextTick(() => (isRestoring = false))
  }

  function currentPayload() {
    const view = listView.value
    return {
      filters: JSON.stringify(view.filters.conditions.value),
      order_by: view.sort.orderBy.value,
      columns: JSON.stringify(view.columns.shown.value),
    }
  }

  const isViewModified = computed(() => {
    const row = activeView.value
    const layout = activeLayout.value
    if (!row || !layout || !listView.value) return false
    const current = currentPayload()
    return (
      current.order_by !== (row.order_by || '') ||
      current.filters !== JSON.stringify(layout.filters) ||
      columnLayout(listView.value.columns.shown.value) !== columnLayout(layout.columns)
    )
  })

  async function createView(label, icon) {
    const doc = await call('frappe.client.insert', {
      doc: {
        doctype: 'HD View',
        label,
        dt: DOCTYPE,
        type: 'list',
        is_customer_portal: 1,
        icon: icon || DEFAULT_VIEW.icon,
        user: sessionUser(),
        ...currentPayload(),
      },
    })
    await list.reload()
    openView(doc.name)
    toast.success(__('View created'))
  }

  async function renameView(name, label, icon) {
    await setValues('HD View', name, { label, icon: icon || DEFAULT_VIEW.icon })
    await list.reload()
  }

  function saveCurrentView(name) {
    return runAction(
      async () => {
        await setValues('HD View', name, currentPayload())
        await list.reload()
        if (name === activeName.value) rememberedLayout.value = null
      },
      { success: __('View updated'), fallback: __('Could not update the view') },
    )
  }

  function deleteView(name) {
    return runAction(
      async () => {
        await call('frappe.client.delete', { doctype: 'HD View', name })
        await list.reload()
        if (activeName.value === name) openView('')
      },
      { success: __('View deleted'), fallback: __('Could not delete the view') },
    )
  }

  function confirmDeleteView(view) {
    askConfirm({
      title: __('Delete {0}', [view.label]),
      message: __('Are you sure you want to delete this view?'),
      label: __('Delete'),
      theme: 'red',
      action: () => deleteView(view.name),
    })
  }

  // Picking a view opens it as saved; the memory is for coming back from elsewhere.
  function openView(name) {
    if (name === activeName.value) {
      rememberedLayout.value = null
      applyActiveView()
      return
    }
    localStorage.removeItem(memoryKey(name))
    navigateTo({ query: name ? { view: name } : {} })
  }

  function openViewModal(mode, view = DEFAULT_VIEW) {
    viewModalMode.value = mode
    viewModalLabel.value = mode === 'rename' ? view.label : ''
    viewModalIcon.value = mode === 'rename' ? view.icon : ''
    viewModalName.value = view.name
    isViewModalOpen.value = true
  }

  const viewOptions = computed(() => [
    {
      group: 'Views',
      hideLabel: true,
      options: [
        { label: __('List'), icon: DEFAULT_VIEW.icon, onClick: () => openView('') },
        ...views.value.map((view) => ({
          name: view.name,
          label: view.label || __('Untitled view'),
          icon: view.icon || DEFAULT_VIEW.icon,
          onClick: () => openView(view.name),
        })),
      ],
    },
    {
      group: 'Actions',
      hideLabel: true,
      options: [
        { label: __('Create View'), icon: 'lucide-plus', onClick: () => openViewModal('create') },
      ],
    },
  ])

  function viewActions(item) {
    if (!item?.name) return []
    return [
      { label: __('Rename'), icon: 'lucide-edit-2', onClick: () => openViewModal('rename', item) },
      { label: __('Delete'), icon: 'lucide-trash-2', onClick: () => confirmDeleteView(item) },
    ]
  }

  function submitViewModal() {
    const label = viewModalLabel.value.trim()
    if (!label) return
    const isRename = viewModalMode.value === 'rename'
    return runAction(
      async () => {
        if (isRename) await renameView(viewModalName.value, label, viewModalIcon.value)
        else await createView(label, viewModalIcon.value)
        isViewModalOpen.value = false
      },
      { fallback: isRename ? __('Could not rename the view') : __('Could not create the view') },
    )
  }

  const bindings = {
    currentView,
    viewOptions,
    viewActions,
    isViewModalOpen,
    viewModalMode,
    viewModalLabel,
    viewModalIcon,
    submitViewModal,
    isViewModified,
    saveViewChanges: () => saveCurrentView(activeName.value),
  }

  return { attachListView, bindings }
}

// Views from the old portal hold a filter dict or wire triples, and wire columns.
function parseViewFilters(raw) {
  const filters = parseJson(raw, [])
  if (Array.isArray(filters) && filters.every((condition) => condition?.fieldname)) return filters
  return toConditions(normalizeFilters(filters))
}

function parseViewColumns(raw) {
  const columns = parseJson(raw, [])
  return columns.every((column) => column?.fieldname) ? columns : parseColumns(columns)
}

// Labels follow the language, not the view.
function columnLayout(columns) {
  return JSON.stringify(columns.map(({ fieldname, width }) => ({ fieldname, width })))
}

// Cloned, so a restore cannot alias the default into live refs.
function snapshotOf(listView) {
  return structuredClone({
    filters: toRaw(listView.filters.conditions.value),
    sort: toRaw(listView.sort.by.value),
    columns: toRaw(listView.columns.shown.value),
  })
}
