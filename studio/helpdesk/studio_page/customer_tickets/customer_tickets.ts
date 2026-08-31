import { computed, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { useListData, useListView } from '@framework/ui/ListView'
import { parseFilters, serializeFilters } from '@framework/ui/Filter'
import {
  loadAssignees,
  avatarCell, datetimeCell, idCell, priorityCell, ratingCell,
  resolutionCell, responseCell, statusCell, subjectCell, textCell,
} from '@app/components/ticketCells'
import { useSettingsModal } from '@app/stores/settings'
import { language, t } from '@app/stores/translations'
import { useViews } from '@app/stores/views'

// Customer-portal Tickets list. Filters, sort, columns and the fetch come from
// @framework/ui's list composables; the columns and cells mirror the agent
// portal's list (HD Ticket's `default_list_data` + Tickets.vue) so the two read
// as one design.
// NOTE: unscoped (all tickets) for demo data — filter by the logged-in
// contact/customer for a real portal.

const DOCTYPE = 'HD Ticket'
const PAGE_LENGTHS = [20, 50, 100]

// HD Ticket's own `default_list_data` (helpdesk/doctype/hd_ticket.py), which is
// what the agent portal's ticket list shows — labels, order and widths alike.
// Kept in English and translated on the way out, so a column's heading can be re-worded
// when the reader changes language without losing the name it is keyed by.
const COLUMN_LABELS = {
  name: 'ID',
  subject: 'Subject',
  status: 'Status',
  response_by: 'First Response',
  resolution_by: 'Resolution',
  _assign: 'Assigned To',
  customer: 'Customer',
  priority: 'Priority',
  ticket_type: 'Type',
  agent_group: 'Team',
  contact: 'Contact',
  feedback_rating: 'Rating',
  creation: 'Created',
}

const DEFAULT_COLUMNS = [
  { fieldname: 'name', width: 'auto' },
  { fieldname: 'subject', width: '25rem' },
  { fieldname: 'status', width: '8rem' },
  { fieldname: 'response_by', width: '8rem' },
  { fieldname: 'resolution_by', width: '8rem' },
  { fieldname: '_assign', width: '8rem' },
  { fieldname: 'customer', width: '8rem' },
  { fieldname: 'priority', width: '10rem' },
  { fieldname: 'ticket_type', width: '11rem' },
  { fieldname: 'agent_group', width: '10rem' },
  { fieldname: 'contact', width: '8rem' },
  { fieldname: 'feedback_rating', width: '10rem' },
  { fieldname: 'creation', width: '8rem' },
].map((column) => ({ ...column, label: t(COLUMN_LABELS[column.fieldname]) }))

// Assignee reads `_assign`, a standard field rather than a docfield. The column
// layer reserves `_`-prefixed keys for host-drawn ("synthetic") columns and drops
// any it has no declaration for, so it is declared here — see `fetchView` below
// for how its data still gets fetched.
const SYNTHETIC_COLUMNS = [{ key: '_assign', label: t('Assigned To'), width: '8rem' }]

// Fields no column shows: whether a first response landed and when the ticket was
// resolved (the SLA badges), plus who has opened it (the subject's unread weight).
// The agent list gets them because `get_list_data` fetches a fixed row set; here
// they ride along as fetch-only keys.
const SUPPORT_FIELDS = ['first_responded_on', 'resolution_date', '_seen']

// Keyed by fieldname, then by column type — the same order `listCell` resolves in.
// `creation`/`modified` are keyed rather than left to the type fallback: neither is
// a docfield, so the column layer has no Meta to call them Datetime with.
const CELLS = {
  name: idCell,
  status: statusCell,
  priority: priorityCell,
  response_by: responseCell,
  resolution_by: resolutionCell,
  creation: datetimeCell,
  modified: datetimeCell,
  _assign: avatarCell,
  feedback_rating: ratingCell,
}
const CELLS_BY_TYPE = { Datetime: datetimeCell, Date: datetimeCell, Rating: ratingCell }

export default function setup(context) {
  // Loaded up front: the organization switcher lists them, and the subject cell
  // needs the reader's email to know which tickets are unread.
  const settings = useSettingsModal(context)
  settings.loadSettings()

  const view = useListView(DOCTYPE, { synthetic: SYNTHETIC_COLUMNS })
  // Seeded before the data layer: `useListData` fetches off the wire columns the
  // moment it is created, so seeding after would spend a request on the defaults.
  view.columns.shown.value = DEFAULT_COLUMNS
  // Headings follow the reader's language, whichever columns they are looking at — the
  // saved view's own picks included, since the label is re-derived rather than restored.
  watch(language, () => {
    view.columns.shown.value = view.columns.shown.value.map((column) => {
      const english = COLUMN_LABELS[column.fieldname || column.key]
      return english ? { ...column, label: t(english) } : column
    })
  })
  // Newest first. Left unset, the list falls back to the server's own order (`modified
  // desc`), which shuffles a ticket to the top whenever anything touches it — including
  // an agent's own edit — so a requester's list never settles.
  view.sort.by.value = [{ fieldname: 'creation', direction: 'desc' }]

  // The fetch skips a synthetic column's key, since normally the host fetches that
  // data itself. `_assign` needs no such help — it is a real column to `get_list` —
  // so the data layer gets the same view with the declarations hidden, plus the
  // support fields appended so they are requested without ever being a column.
  const fetchView = {
    ...view,
    columns: {
      ...view.columns,
      synthetic: computed(() => []),
      wire: computed(() => [
        ...view.columns.wire.value,
        ...SUPPORT_FIELDS.map((key) => ({ key })),
      ]),
    },
  }
  const data = useListData(DOCTYPE, fetchView)

  // Who the assignees are, fetched as rows arrive: `_assign` is only user ids, and the
  // Assigned To column draws a face and a name from them.
  watch(data.rows, (rows) => loadAssignees(rows), { immediate: true })

  // Saved views. Bound after the view exists so it can restore into it; the store reads
  // `?view=` off the route, so a shared URL opens the same layout.
  const views = useViews(context, view)

  const listColumns = computed(() =>
    view.columns.wire.value.map((column) => ({ ...column, cell: cellFor(column) })),
  )

  function cellFor(column) {
    // Subject alone needs context beyond the row: who is reading. `_seen` holds
    // User docnames, not emails.
    if (column.key === 'subject')
      return (props) => subjectCell(props, settings.settingsUser.value.name)
    return CELLS[column.key] || CELLS_BY_TYPE[column.type] || textCell
  }

  const emptyState = computed(() => ({
    title: 'No tickets found',
    description: view.filters.conditions.value.length
      ? 'No tickets match the applied filters. Try adjusting or clearing them.'
      : 'Tickets you raise will show up here.',
  }))

  // Stays inside the portal now that it has a ticket page of its own; it used to
  // hand the reader over to the desk SPA and its own chrome.
  function openTicket(row) {
    context.router.push('/tickets/' + row.name)
  }

  // --- Organization switcher ---

  // The switcher is a view of the `customer` condition, not state beside it: clear
  // that condition from the Filter panel and the switcher follows.
  const selectedOrganizations = computed(() => {
    const condition = view.filters.conditions.value.find(isCustomerCondition)
    if (!condition) return []
    return Array.isArray(condition.value) ? condition.value : [condition.value]
  })

  function selectOrganization(customers) {
    const others = view.filters.conditions.value.filter((c) => !isCustomerCondition(c))
    view.filters.conditions.value = customers?.length
      ? [...others, { fieldname: 'customer', operator: 'in', value: customers }]
      : others
  }

  // `equals` too, so a condition set from the Filter panel — or left by the
  // single-select this replaced — is still the one the switcher reflects.
  function isCustomerCondition(condition) {
    return (
      condition.fieldname === 'customer' &&
      (condition.operator === 'in' || condition.operator === 'equals')
    )
  }

  // --- Filter ---

  // The agent portal's own filter control, ported into this app (KbFilter.vue). It speaks
  // Frappe wire conditions, so the page translates on both sides: `serializeFilters` down
  // to tuples for the control, `parseFilters` back up to the condition objects the list
  // data layer and the QuickFilter share.
  //
  // Fields come from the same endpoint the agent list uses, asked with the customer-portal
  // flag so it offers only what a requester may filter on.
  const filterFields = createResource({
    url: 'helpdesk.api.doc.get_filterable_fields',
    cache: ['HD Ticket', 'customer-portal-filter-fields'],
    params: { doctype: DOCTYPE, show_customer_portal_fields: true },
    auto: true,
  })

  const filterConditions = computed({
    get: () => serializeFilters(view.filters.conditions.value),
    set: (wire) => {
      view.filters.conditions.value = parseFilters(filterFields.data || [], wire)
    },
  })

  // One organization is not a choice. Scope the list to it as soon as it is known, rather
  // than showing an empty switcher the reader has to operate to name the only place they
  // belong. Skipped when a condition is already there — a remembered search, or their own
  // pick — so this never overrides what they chose.
  watch(
    settings.organizations,
    (orgs) => {
      if (orgs.length !== 1 || selectedOrganizations.value.length) return
      selectOrganization([orgs[0].name])
    },
    { immediate: true },
  )

  // Customer is in `in_standard_filter`, so it arrives as a quick filter — but the
  // switcher is that filter here. Writable so customize mode still writes back.
  const quickFilterFields = computed({
    get: () => view.quickFilter.fields.value.filter((f) => f.fieldname !== 'customer'),
    set: (fields) => (view.quickFilter.fields.value = fields),
  })

  return {
    ...settings,
    ...views,
    navMenuOpen: ref(false),
    // toolbar control state
    selectedOrganizations,
    selectOrganization,
    filters: view.filters.conditions,
    sort: view.sort.by,
    columns: view.columns.shown,
    // ColumnSettings offers its picker options from its own prop, not the composable.
    syntheticColumns: SYNTHETIC_COLUMNS,
    quickFilterFields,
    quickFilterCustomizing: view.quickFilter.customizing,
    // the ported filter control
    filterFields: computed(() => filterFields.data || []),
    filterConditions,
    setFilterConditions: (wire) => (filterConditions.value = wire),
    // table + footer
    listColumns,
    emptyState,
    openTicket,
    rows: data.rows,
    listLoading: data.loading,
    rowCount: data.rowCount,
    totalCount: data.totalCount,
    pageLength: data.pageLength,
    pageLengthOptions: PAGE_LENGTHS,
    loadMore: data.loadMore,
    reload: data.reload,
    resizeColumn: ({ key, width }) => view.columns.setWidth(key, width),
  }
}
