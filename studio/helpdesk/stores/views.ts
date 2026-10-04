import { computed, nextTick, ref, shallowRef, toRaw, watch } from 'vue'
import { StorageSerializers, useStorage } from '@vueuse/core'
import { call, createListResource, toast } from 'frappe-ui'
import { spritePlugin } from 'frappe-ui/experimental'
import { parseOrderBy } from '@framework/ui/SortBy'
import { __ } from '@helpdesk/shared/translation'
import { currentRoute, navigateTo } from '@app/stores/router'
import { useSession } from '@app/stores/session'
import { parseJson } from '@app/utils'


// ponytail: Studio dropped the lucide sprite, but view icons are any lucide name stored per
// view, which build-time classes cannot cover. Move off it before frappe-ui removes it.
if (!document.getElementById('lucide-sprite')) spritePlugin.install()

const DOCTYPE = 'HD Ticket'

const DEFAULT_VIEW = { name: '', label: 'List', icon: 'text-align-justify' }

// Storage, not the URL: every way back into this list pushes a bare `/customer-tickets`.
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
    filters: { dt: DOCTYPE, is_customer_portal: 1 },
    pageLength: 1000,
  })

  // `if_owner` covers HD Customer but not the Agent roles, who would see everyone's views.
  const views = computed(() => list.data || [])

  const listView = shallowRef(null) // the page's useListView
  let hasAttached = false
  let defaultSnapshot = null // the page's own layout, restored by the unnamed "List" view
  let isRestoring = false // guards the remember-watch while a restore writes the refs

  const isViewModalOpen = ref(false)
  const viewModalMode = ref('create') // 'create' | 'rename'
  const viewModalLabel = ref('')
  const viewModalIcon = ref('')
  const viewModalName = ref('')

  const activeName = computed(() => currentRoute().query?.view || '')

  const activeView = computed(
    () => views.value.find((view) => view.name === activeName.value) || null,
  )

  const currentView = computed(() =>
    activeView.value
      ? { ...activeView.value, icon: activeView.value.icon || DEFAULT_VIEW.icon }
      : DEFAULT_VIEW,
  )

  const rememberedLayout = useStorage(
    () => `${MEMORY_PREFIX}:${DOCTYPE}:${activeName.value}`,
    null,
    localStorage,
    { serializer: StorageSerializers.object, writeDefaults: false },
  )

  // Here, not in attachListView: Studio stops the page's effect scope on navigation.
  // On route change, not on click, so a shared URL lands on the same view.
  watch(() => [activeName.value, list.data], () => applyActiveView())
  watch(
    () => listView.value && [listView.value.filters.conditions.value, listView.value.sort.by.value],
    () => rememberLayout(),
    { deep: true },
  )

  function attachListView(view) {
    // This store outlives the page, so never hold the first mount's `useListView`.
    listView.value = view
    // On every mount: the watch above fires on neither a same-view return nor a remount.
    applyActiveView()
    if (hasAttached) return
    hasAttached = true
    // The page's default columns, or leaving a saved view would restore no columns at all.
    defaultSnapshot = snapshotOf(view)
    // The fetch waits for the session: an empty owner would return nothing, silently.
    useSession()
      .loadSession()
      .then(() => {
        list.update({ filters: { ...list.filters, owner: sessionUser() } })
        return list.reload()
      })
  }

  function rememberLayout() {
    const view = listView.value
    if (isRestoring || !view) return
    rememberedLayout.value = {
      filters: view.filters.conditions.value,
      sort: view.sort.by.value,
    }
  }

  function applyActiveView() {
    const view = listView.value
    if (!view) return
    isRestoring = true
    const row = activeView.value
    if (!row) {
      if (defaultSnapshot) view.restore(structuredClone(defaultSnapshot))
    } else {
      view.restore({
        filters: parseJson(row.filters, []),
        sort: parseOrderBy(row.order_by || ''),
        columns: parseJson(row.columns, []),
      })
    }
    // After the view, never instead of it. An empty sort means the reader never chose one.
    const remembered = rememberedLayout.value
    if (remembered) {
      view.restore({
        filters: remembered.filters,
        ...(remembered.sort?.length ? { sort: remembered.sort } : {}),
      })
    }
    // Next tick, so the restore's own writes do not re-record what was just read.
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
    toast.success(__('View "{0}" created', [label]))
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
    toast.success(__('View updated'))
  }

  async function deleteView(name) {
    await call('frappe.client.delete', { doctype: 'HD View', name })
    await list.reload()
    if (activeName.value === name) openView('')
  }

  function openView(name) {
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
        { label: DEFAULT_VIEW.label, icon: DEFAULT_VIEW.icon, onClick: () => openView('') },
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
        { label: __('Save as new view'), icon: 'lucide-plus', onClick: () => openViewModal('create') },
      ],
    },
  ])

  function viewActions(item) {
    if (!item?.name) return []
    return [
      { label: __('Save current layout'), icon: 'lucide-save', onClick: () => saveCurrentView() },
      { label: __('Rename'), icon: 'lucide-edit-2', onClick: () => openViewModal('rename', item) },
      { label: __('Delete'), icon: 'lucide-trash-2', onClick: () => deleteView(item.name) },
    ]
  }

  function submitViewModal() {
    const label = viewModalLabel.value.trim()
    if (!label) return
    const done =
      viewModalMode.value === 'rename'
        ? renameView(viewModalName.value, label, viewModalIcon.value)
        : createView(label, viewModalIcon.value)
    return done.then(() => (isViewModalOpen.value = false))
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
  }

  return { attachListView, bindings }
}

// Copied, so a restore cannot alias the stored default into live refs.
function snapshotOf(listView) {
  return structuredClone({
    filters: toRaw(listView.filters.conditions.value),
    sort: toRaw(listView.sort.by.value),
    columns: toRaw(listView.columns.shown.value),
  })
}
