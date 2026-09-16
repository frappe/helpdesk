import { computed, ref, watch } from 'vue'
import { ROUTES } from '@app/routes'
import { createResource } from 'frappe-ui'
import { useListData, useListView } from '@framework/ui/ListView'
import { parseFilters, serializeFilters } from '@framework/ui/Filter'
import {
  loadAssignees,
  avatarCell, datetimeCell, idCell, priorityCell, ratingCell,
  resolutionCell, responseCell, statusCell, subjectCell, textCell,
} from '@app/components/list/ticketCells'
import { useSettingsModal } from '@app/stores/settings'
import { language, t } from '@app/stores/translations'
import { useViews } from '@app/stores/views'

// No client-side scoping: HD Ticket's permission_query already limits a non-agent to
// their own tickets plus those of customers they manage.

const DOCTYPE = 'HD Ticket'
const PAGE_LENGTHS = [20, 50, 100]

// Kept in English and translated on the way out, so a heading survives a language change.
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

// The column layer drops `_`-prefixed keys it has no declaration for.
const SYNTHETIC_COLUMNS = [{ key: '_assign', label: t('Assigned To'), width: '8rem' }]

// Fetch-only: the SLA badges and the subject's unread weight need these, no column shows them.
const SUPPORT_FIELDS = ['first_responded_on', 'resolution_date', '_seen']

// `creation`/`modified` are keyed, not left to the type fallback: neither is a docfield.
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
  // The switcher lists them and the subject cell needs the reader's email for unread.
  const settings = useSettingsModal(context)
  settings.loadSettings()

  const view = useListView(DOCTYPE, { synthetic: SYNTHETIC_COLUMNS })
  // Before the data layer: `useListData` fetches on creation, so seeding after costs a request.
  view.columns.shown.value = DEFAULT_COLUMNS
  watch(language, () => {
    view.columns.shown.value = view.columns.shown.value.map((column) => {
      const english = COLUMN_LABELS[column.fieldname || column.key]
      return english ? { ...column, label: t(english) } : column
    })
  })
  // Unset, the server orders by `modified`, which never settles for a requester.
  view.sort.by.value = [{ fieldname: 'creation', direction: 'desc' }]

  // The fetch skips synthetic keys, but `_assign` is a real column to `get_list`.
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

  // `_assign` is only user ids; the column draws a face and a name from them.
  watch(data.rows, (rows) => loadAssignees(rows), { immediate: true })

  const views = useViews(context, view)

  const listColumns = computed(() =>
    view.columns.wire.value.map((column) => ({ ...column, cell: cellFor(column) })),
  )

  function cellFor(column) {
    // `_seen` holds User docnames, not emails.
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

  function openTicket(row) {
    context.router.push(ROUTES.ticket(row.name))
  }

  // --- Organization switcher ---

  // A view of the `customer` condition, not state beside it.
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

  // `equals` too, so a condition set from the Filter panel is still reflected.
  function isCustomerCondition(condition) {
    return (
      condition.fieldname === 'customer' &&
      (condition.operator === 'in' || condition.operator === 'equals')
    )
  }

  // --- Filter ---

  // The customer-portal flag limits this to what a requester may filter on.
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

  // One organization is not a choice, but never override a condition already there.
  watch(
    settings.organizations,
    (orgs) => {
      if (orgs.length !== 1 || selectedOrganizations.value.length) return
      selectOrganization([orgs[0].name])
    },
    { immediate: true },
  )

  // Customer arrives as a quick filter, but the switcher is that filter here.
  const quickFilterFields = computed({
    get: () => view.quickFilter.fields.value.filter((f) => f.fieldname !== 'customer'),
    set: (fields) => (view.quickFilter.fields.value = fields),
  })

  return {
    ...settings,
    ...views,
    navMenuOpen: ref(false),
    selectedOrganizations,
    selectOrganization,
    filters: view.filters.conditions,
    sort: view.sort.by,
    columns: view.columns.shown,
    // ColumnSettings reads its picker options from this prop, not the composable.
    syntheticColumns: SYNTHETIC_COLUMNS,
    quickFilterFields,
    quickFilterCustomizing: view.quickFilter.customizing,
    filterFields: computed(() => filterFields.data || []),
    filterConditions,
    setFilterConditions: (wire) => (filterConditions.value = wire),
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
