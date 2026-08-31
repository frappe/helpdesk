import { computed, nextTick, ref, watch } from 'vue'
import { call, createListResource, toast } from 'frappe-ui'
import { parseOrderBy, serializeOrderBy } from '@framework/ui/SortBy'
import { useSession } from '@app/stores/session'

// Saved list views for the customer portal — this portal is the only reader.
//
// Filter conditions are stored whole, exactly as `useListView.snapshot` hands them over:
// they carry their own field Meta, so a round-trip needs no doctype lookup and is
// lossless (two conditions on one field included). Sort keeps the readable `order_by`
// string form, which round-trips losslessly since a Sort is just fieldname + direction.

const DOCTYPE = 'HD Ticket'

// What the breadcrumb shows before any saved view is picked. Mirrors the desk's
// `currentView` default (label "List", an align-justify glyph).
const DEFAULT_VIEW = { name: '', label: 'List', icon: 'text-align-justify' }

// Where a list's working state waits while the reader is off reading a ticket. The desk
// keeps the equivalent in the URL (`?filters=`) and leans on localStorage for the parts a
// URL cannot carry — page length, scroll position. Here it has to be storage: every way
// back into this list (breadcrumb, account menu, post-submit redirect) pushes a bare
// `/customer-tickets`, so a query string would survive the Back button and nothing else.
const MEMORY_PREFIX = 'kb-list'

const store = createViewsStore()

/** `listView` is the page's `useListView` — the snapshot source and restore target. */
export function useViews(context, listView) {
  store.bind(context, listView)
  return store
}

/** Already loaded by the page (the settings modal pulls the session in), so this is a
 *  read of state that is there, not a second fetch. */
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

  // Scoped to the reader explicitly rather than leaning on permissions: `HD Customer` is
  // `if_owner` on HD View, but the `Agent` roles are not — so an agent opening this
  // portal would otherwise be shown every customer's saved views. The desk's customer
  // portal guards the same way (`filters.user`).
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
    // Always the current page's composable: this store outlives the page, and holding the
    // first mount's `useListView` meant every later visit restored into a discarded one.
    view = listView
    // Straight away, and on every mount: the watch below only fires when the view name or
    // the fetched rows change, and a reader coming back to the same view changes neither.
    applyActiveView()
    if (bound) return
    bound = true
    // The page seeds its default columns before binding, so this captures them as the
    // layout the unnamed "List" view restores to. Without it, leaving a saved view would
    // reset to *no* columns and the table would render blank rows.
    //
    // Only the three parts a view persists. `quickFilterFields` is deliberately excluded:
    // it resolves asynchronously from Meta, so capturing it here would snapshot an empty
    // strip and restoring that would wipe the Subject/Name quick filters — and the page
    // owns that set anyway (it hides `customer`, which the org switcher stands in for).
    defaultSnapshot = snapshotOf(listView)
    // Who the reader is arrives over the wire, so the fetch waits for it — filtering on
    // an empty owner would quietly return nothing and every saved view would vanish.
    // `owner` rather than `user`: it is what the `if_owner` rule keys on, and the server
    // sets it on insert, so it is right even for rows written before `user` was.
    useSession(context)
      .loadSession()
      .then(() => {
        list.update({ filters: { ...list.filters, owner: sessionUser() } })
        return list.reload()
      })
    // Applying happens on route change, not on click, so a shared/reloaded URL lands on
    // the same view the author saw.
    watch(
      () => [activeName.value, list.data],
      () => applyActiveView(),
    )
    // Whatever the reader narrows to is theirs until they change it — remembered per view,
    // so switching views does not carry one view's search into another.
    watch(
      () => [view.filters.conditions.value, view.sort.by.value],
      () => remember(),
      { deep: true },
    )
  }

  /** The working state a reader builds up on top of a view: what they searched and how they
   *  sorted it. Columns are left out — those belong to the view itself. */
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

  /** Seed the list view from the stored row — the load half of the snapshot contract —
   *  then lay the reader's own search back over it. */
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
    // After the view, never instead of it: the view supplies the columns and its own
    // starting point, and this is the narrowing the reader did on top of that.
    const working = read(memoryKey())
    // An empty sort means the reader never chose one, not that they cleared the page's
    // default — restoring it wiped the list's own "newest first" on every visit.
    if (working) {
      view.restore({
        filters: working.filters,
        ...(working.sort?.length ? { sort: working.sort } : {}),
      })
    }
    // Released on the next tick so the restore's own writes do not re-record what was
    // just read — `restore` reassigns the refs, and the watch runs after this returns.
    nextTick(() => (restoring = false))
  }

  /** The save half — the persisted slice of the current snapshot. */
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

  /** Overwrite a saved view with what is on screen now. */
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
        // Legacy rows exist with a null label; they'd otherwise render as a blank menu
        // row you can click but not identify.
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

  /** Kebab actions on a single saved view. The default "List" row has no `name`. */
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
    // A page-script binding can't be a Studio `$type: variable`, so the dialog reads
    // through the prop and writes back through an `update:modelValue` Run Script.
    setViewModal: (value) => (modal.value = value),
    submitViewModal: submitModal,
    saveCurrentView,
    deleteView,
  }
}

/** The persisted slice of a view's snapshot — filters, sort and columns, the same three
 *  the desk stores on `HD View`. Structurally copied: snapshots are plain JSON by
 *  contract, and this keeps a restore from aliasing the stored default into live refs. */
function snapshotOf(listView) {
  return clone({
    filters: listView.filters.conditions.value,
    sort: listView.sort.by.value,
    columns: listView.columns.shown.value,
  })
}

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function parseJson(value, fallback) {
  if (!value) return fallback
  if (typeof value !== 'string') return value
  try {
    return JSON.parse(value) ?? fallback
  } catch {
    return fallback
  }
}
