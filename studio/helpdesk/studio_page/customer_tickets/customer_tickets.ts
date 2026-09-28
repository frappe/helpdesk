import { computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { useListData, useListView } from '@framework/ui/ListView'
import { parseFilters, serializeFilters } from '@framework/ui/Filter'
import { __, translations } from '@helpdesk/shared/translation'
import {
  datetimeCell, idCell, priorityCell, ratingCell,
  resolutionCell, responseCell, statusCell, subjectCell, textCell,
} from '@app/components/list/ticketCells'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { useViews } from '@app/stores/views'

// No client-side scoping: HD Ticket's permission_query already limits a non-agent to
// their own tickets plus those of customers they manage.

const DOCTYPE = 'HD Ticket'
const PAGE_LENGTH_OPTIONS = [20, 50, 100]

// Kept in English and translated on the way out, so a heading survives a language change.
const COLUMN_LABELS = {
  name: 'ID',
  subject: 'Subject',
  status: 'Status',
  response_by: 'First Response',
  resolution_by: 'Resolution',
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
  { fieldname: 'customer', width: '8rem' },
  { fieldname: 'priority', width: '10rem' },
  { fieldname: 'ticket_type', width: '11rem' },
  { fieldname: 'agent_group', width: '10rem' },
  { fieldname: 'contact', width: '8rem' },
  { fieldname: 'feedback_rating', width: '10rem' },
  { fieldname: 'creation', width: '8rem' },
].map((column) => ({ ...column, label: __(COLUMN_LABELS[column.fieldname]) }))

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
  feedback_rating: ratingCell,
}
const CELLS_BY_TYPE = { Datetime: datetimeCell, Date: datetimeCell, Rating: ratingCell }

export default function setup(context) {
  // The switcher lists them and the subject cell needs the reader's email for unread.
  const settings = useSettingsModal(context)
  settings.loadSettings()

  const view = useListView(DOCTYPE)
  // Before the data layer: `useListData` fetches on creation, so seeding after costs a request.
  view.columns.shown.value = DEFAULT_COLUMNS
  watch(translations, () => {
    view.columns.shown.value = view.columns.shown.value.map((column) => {
      const english = COLUMN_LABELS[column.fieldname || column.key]
      return english ? { ...column, label: __(english) } : column
    })
  })
  // Unset, the server orders by `modified`, which never settles for a requester.
  view.sort.by.value = [{ fieldname: 'creation', direction: 'desc' }]

  const fetchView = {
    ...view,
    columns: {
      ...view.columns,
      wire: computed(() => [
        ...view.columns.wire.value,
        ...SUPPORT_FIELDS.map((key) => ({ key })),
      ]),
    },
  }
  const data = useListData(DOCTYPE, fetchView)

  const views = useViews(view)

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
    title: __('No tickets found'),
    description: view.filters.conditions.value.length
      ? __('No tickets match the applied filters. Try adjusting or clearing them.')
      : __('Tickets you raise will show up here.'),
  }))

  function openTicket(row) {
    navigateTo(ROUTES.ticket(row.name))
  }

  // A view of the `customer` condition, not state beside it.
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
    (organizations) => {
      if (organizations.length !== 1 || selectedOrganizations.value.length) return
      selectOrganization([organizations[0].name])
    },
    { immediate: true },
  )

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
    pageLengthOptions: PAGE_LENGTH_OPTIONS,
    loadMore: data.loadMore,
    reload: data.reload,
    resizeColumn: ({ key, width }) => view.columns.setWidth(key, width),
  }
}
