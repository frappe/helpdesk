import { computed, nextTick, ref, watch } from 'vue'
import { clone, parseJson } from '@app/utils'
import { call, createListResource, toast } from 'frappe-ui'
import { parseOrderBy, serializeOrderBy } from '@framework/ui/SortBy'
import { useSession } from '@app/stores/session'

// Conditions are stored whole as `snapshot` hands them over: lossless, no doctype lookup.

const DOCTYPE = 'HD Ticket'

const DEFAULT_VIEW = { name: '', label: 'List', icon: 'text-align-justify' }

// Storage, not the URL: every way back into this list pushes a bare `/customer-tickets`.
const MEMORY_PREFIX = 'kb:list'

const store = createViewsStore()

export function useViews(context, listView) {
  store.bind(context, listView)
  return store
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
    filters: { dt: DOCTYPE, is_customer_portal: 1 },
    pageLength: 1000,
  })

  // `if_owner` covers HD Customer but not the Agent roles, who would see everyone's views.
  const views = computed(() => list.data || [])

  let router = null
  let route = null
  let view = null            // the page's useListView
  let bound = false
  let defaultSnapshot = null // the page's own layout, restored by the unnamed "List" view
  let restoring = false      // guards the remember-watch while a restore writes the refs

  const modal = ref({ show: false, mode: 'create', label: '', icon: '' })

  function bind(context, listView) {
    router = router || context?.router
    route = route || context?.route
    // This store outlives the page, so never hold the first mount's `useListView`.
    view = listView
    // On every mount: the watch below fires on neither a same-view return nor a remount.
    applyActiveView()
    if (bound) return
    bound = true
    // The page's default columns, or leaving a saved view would restore no columns at all.
    defaultSnapshot = snapshotOf(listView)
    // The fetch waits for the session: an empty owner would return nothing, silently.
    useSession(context)
      .loadSession()
      .then(() => {
        list.update({ filters: { ...list.filters, owner: sessionUser() } })
        return list.reload()
      })
    // On route change, not on click, so a shared URL lands on the same view.
    watch(
      () => [activeName.value, list.data],
      () => applyActiveView(),
    )
    // Remembered per view, so switching does not carry one view's search into another.
    watch(
      () => [view.filters.conditions.value, view.sort.by.value],
      () => remember(),
      { deep: true },
    )
  }

  // Columns are left out: those belong to the view itself.
  function remember() {
    if (restoring || !view) return
    write(memoryKey(), {
      filters: view.filters.conditions.value,
      sort: view.sort.by.value,
    })
  }

  function memoryKey() {
    return `${MEMORY_PREFIX}:${DOCTYPE}:${activeName.value}`
  }

  function write(key: string, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value))
    } catch {
      // A browser with storage refused (private mode, quota) still gets a working list.
    }
  }

  function read(key: string) {
    try {
      return JSON.parse(window.localStorage.getItem(key) || 'null')
    } catch {
      return null
    }
  }

  const activeName = computed(() => route?.query?.view || '')

  const activeView = computed(
    () => views.value.find((v) => v.name === activeName.value) || null,
  )

  const currentView = computed(() =>
    activeView.value
      ? { ...activeView.value, icon: activeView.value.icon || DEFAULT_VIEW.icon }
      : DEFAULT_VIEW,
  )

  function applyActiveView() {
    if (!view) return
    restoring = true
    const row = activeView.value
    // No `?view=` — the unnamed "List" view, i.e. the page's own default layout.
    if (!row) {
      if (defaultSnapshot) view.restore(clone(defaultSnapshot))
    } else {
      view.restore({
        filters: parseJson(row.filters, []),
        sort: parseOrderBy(row.order_by || ''),
        columns: parseJson(row.columns, []),
      })
    }
    // After the view, never instead of it.
    const working = read(memoryKey())
    // An empty sort means the reader never chose one, not that they cleared the default.
    if (working) {
      view.restore({
        filters: working.filters,
        ...(working.sort?.length ? { sort: working.sort } : {}),
      })
    }
    // Next tick, so the restore's own writes do not re-record what was just read.
    nextTick(() => (restoring = false))
  }

  function currentPayload() {
    return {
      filters: JSON.stringify(view.filters.conditions.value),
      order_by: view.sort.orderBy.value,
      columns: JSON.stringify(view.columns.shown.value),
    }
  }

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
    open(doc.name)
    toast.success(`View "${label}" created`)
  }

  async function renameView(name, label, icon) {
    await call('frappe.client.set_value', {
      doctype: 'HD View',
      name,
      fieldname: { label, icon: icon || DEFAULT_VIEW.icon },
    })
    await list.reload()
  }

  async function saveCurrentView() {
    if (!activeView.value) return
    await call('frappe.client.set_value', {
      doctype: 'HD View',
      name: activeView.value.name,
      fieldname: currentPayload(),
    })
    await list.reload()
    toast.success('View updated')
  }

  async function deleteView(name) {
    await call('frappe.client.delete', { doctype: 'HD View', name })
    await list.reload()
    if (activeName.value === name) open('')
  }

  function open(name) {
    router?.push({ query: name ? { view: name } : {} })
  }

  // --- what the breadcrumb dropdown renders ---

  const options = computed(() => [
    {
      group: 'Views',
      hideLabel: true,
      items: [
        { label: DEFAULT_VIEW.label, icon: DEFAULT_VIEW.icon, onClick: () => open('') },
        // Legacy rows with a null label would render as a blank, unidentifiable row.
        ...views.value.map((v) => ({
          name: v.name,
          label: v.label || 'Untitled view',
          icon: v.icon || DEFAULT_VIEW.icon,
          onClick: () => open(v.name),
        })),
      ],
    },
    {
      group: 'Actions',
      hideLabel: true,
      items: [
        {
          label: 'Save as new view',
          icon: 'plus',
          onClick: () =>
            (modal.value = { show: true, mode: 'create', label: '', icon: '' }),
        },
      ],
    },
  ])

  // The default "List" row has no `name`.
  function viewActions(item) {
    if (!item?.name) return []
    return [
      {
        label: 'Save current layout',
        icon: 'save',
        onClick: () => saveCurrentView(),
      },
      {
        label: 'Rename',
        icon: 'edit-2',
        onClick: () =>
          (modal.value = {
            show: true,
            mode: 'rename',
            label: item.label,
            icon: item.icon,
            name: item.name,
          }),
      },
      { label: 'Delete', icon: 'trash-2', onClick: () => deleteView(item.name) },
    ]
  }

  function submitModal() {
    const { mode, label, icon, name } = modal.value
    const trimmed = (label || '').trim()
    if (!trimmed) return
    const done =
      mode === 'rename' ? renameView(name, trimmed, icon) : createView(trimmed, icon)
    return done.then(() => (modal.value = { ...modal.value, show: false }))
  }

  return {
    bind,
    viewsList: views,
    currentView,
    viewOptions: options,
    viewActions,
    viewModal: modal,
    // A page-script binding can't be a Studio `$type: variable`.
    setViewModal: (value) => (modal.value = value),
    submitViewModal: submitModal,
    saveCurrentView,
    deleteView,
  }
}

// Copied, so a restore cannot alias the stored default into live refs.
function snapshotOf(listView) {
  return clone({
    filters: listView.filters.conditions.value,
    sort: listView.sort.by.value,
    columns: listView.columns.shown.value,
  })
}

