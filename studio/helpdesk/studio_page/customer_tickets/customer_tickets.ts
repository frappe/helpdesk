import { computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { useListData, useListView } from '@framework/ui/ListView'
import { __, translations } from '@helpdesk/shared/translation'
import {
  datetimeCell, idCell, priorityCell, ratingCell,
  resolutionCell, responseCell, statusCell, subjectCell, textCell,
} from '@app/components/list/ticketCells'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { useViews } from '@app/stores/views'

// HD Ticket's permission_query already scopes the rows to what the requester may see.
const DOCTYPE = 'HD Ticket'
const PAGE_LENGTH_OPTIONS = [20, 50, 100]

// A function, so headings follow a language change; literal `__()` calls, so they extract.
function columnLabels() {
  return {
    name: __('ID'),
    subject: __('Subject'),
    status: __('Status'),
    response_by: __('First Response'),
    resolution_by: __('Resolution'),
    customer: __('Customer'),
    priority: __('Priority'),
    ticket_type: __('Type'),
    agent_group: __('Team'),
    contact: __('Contact'),
    feedback_rating: __('Rating'),
    creation: __('Created'),
  }
}

const DEFAULT_COLUMNS = [
  { fieldname: 'name', width: 'auto' },
  { fieldname: 'subject', width: '25rem' },
  { fieldname: 'status', width: '8rem' },
  { fieldname: 'priority', width: '10rem' },
  { fieldname: 'response_by', width: '8rem' },
  { fieldname: 'resolution_by', width: '8rem' },
  { fieldname: 'creation', width: '8rem' },
]

// Always fetched: the phone rows, SLA badges and unread subjects read them whatever the columns.
const PHONE_FIELDS = ['subject', 'creation', 'status', 'name']
const SUPPORT_FIELDS = ['sla', 'first_responded_on', 'resolution_date', '_seen', ...PHONE_FIELDS]

// `creation`/`modified` are keyed, not left to the type fallback: neither is a docfield.
const CELLS = {
  name: idCell,
  status: statusCell,
  priority: priorityCell,
  response_by: responseCell,
  resolution_by: resolutionCell,
  creation: datetimeCell,
  modified: datetimeCell,
  feedback_rating: ratingCell,
}
const CELLS_BY_TYPE = { Datetime: datetimeCell, Date: datetimeCell, Rating: ratingCell }

// `useListData` refetches on every new identity, even when the request is unchanged.
function settled(source) {
  let last
  return computed(() => {
    const next = source()
    return JSON.stringify(next) === JSON.stringify(last) ? last : (last = next)
  })
}

function withLabel(column) {
  const label = columnLabels()[column.fieldname || column.key]
  return label ? { ...column, label } : column
}

export default function setup(context) {
  const settings = useSettingsModal(context)
  settings.loadSettings()

  // Seeded before `useListData`, which fetches on creation.
  const view = useListView(DOCTYPE)
  view.columns.shown.value = DEFAULT_COLUMNS.map(withLabel)
  watch(translations, () => (view.columns.shown.value = view.columns.shown.value.map(withLabel)))
  view.sort.by.value = [{ fieldname: 'creation', direction: 'desc' }]
  const views = useViews(view)

  const fetchView = {
    ...view,
    filters: { ...view.filters, wire: settled(() => view.filters.wire.value) },
    columns: {
      ...view.columns,
      wire: settled(() =>
        [...new Set([...view.columns.wire.value.map((column) => column.key), ...SUPPORT_FIELDS])].map(
          (key) => ({ key }),
        ),
      ),
    },
  }
  const data = useListData(DOCTYPE, fetchView)

  const listColumns = computed(() =>
    settings.isPhone.value
      ? PHONE_FIELDS.map((key) => ({ key, cell: cellFor({ key }) }))
      : view.columns.wire.value.map((column) => ({ ...column, cell: cellFor(column) })),
  )

  function cellFor(column) {
    // `_seen` holds User docnames, not emails.
    if (column.key === 'subject')
      return (props) => subjectCell(props, settings.settingsUser.value.name)
    return CELLS[column.key] || CELLS_BY_TYPE[column.type] || textCell
  }

  const emptyState = computed(() => ({
    title: __('No tickets found'),
    description: view.filters.conditions.value.length
      ? __('No tickets match the applied filters. Try adjusting or clearing them.')
      : __('Tickets you raise will show up here.'),
  }))

  function openTicket(row) {
    navigateTo(ROUTES.ticket(row.name))
  }

  const selectedOrganizations = computed(() => {
    const condition = view.filters.conditions.value.find(isCustomerCondition)
    if (!condition) return []
    return Array.isArray(condition.value) ? condition.value : [condition.value]
  })

  function selectOrganization(customers) {
    const others = view.filters.conditions.value.filter(
      (condition) => !isCustomerCondition(condition),
    )
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

  const filterFields = createResource({
    url: 'helpdesk.api.doc.get_filterable_fields',
    cache: ['HD Ticket', 'customer-portal-filter-fields'],
    params: { doctype: DOCTYPE, show_customer_portal_fields: true },
    auto: true,
  })

  // Customer arrives as a quick filter, but the switcher is that filter here.
  const quickFilterFields = computed({
    get: () => view.quickFilter.fields.value.filter((field) => field.fieldname !== 'customer'),
    set: (fields) => (view.quickFilter.fields.value = fields),
  })

  return {
    ...settings,
    ...views,
    selectedOrganizations,
    selectOrganization,
    filters: view.filters.conditions,
    sort: view.sort.by,
    columns: view.columns.shown,
    quickFilterFields,
    quickFilterCustomizing: view.quickFilter.customizing,
    filterFields: computed(() => filterFields.data || []),
    listColumns,
    emptyState,
    openTicket,
    pageActionLabel: computed(() => (settings.canCreateTicket.value ? __('Raise a ticket') : '')),
    pageActionIcon: 'lucide-plus',
    onPageAction: () => navigateTo(ROUTES.newTicket),
    rows: data.rows,
    listLoading: data.loading,
    rowCount: data.rowCount,
    totalCount: data.totalCount,
    pageLength: data.pageLength,
    pageLengthOptions: PAGE_LENGTH_OPTIONS,
    loadMore: data.loadMore,
    reload: data.reload,
    resizeColumn: ({ key, width }) => view.columns.setWidth(key, width),
  }
}
