# Full-Text Search Implementation Plan for Helpdesk (Corrected)

## Overview

This document outlines the corrected implementation plan for adding full-text search capabilities to Frappe Helpdesk using SQLite FTS (Full-Text Search), following the pattern established in Gameplan. The search will enable agents and customers to quickly find tickets, comments, and communications through a dedicated search page with advanced filtering capabilities.

## Current State Analysis

### Existing Helpdesk Search
- **Current Implementation**: Redis-based search in `helpdesk/helpdesk/search.py` using RediSearch
- **Indexed Documents**: HD Ticket, HD Article
- **Command Palette**: Basic implementation in `helpdesk/desk/src/components/command-palette/CP.vue`
- **Search API**: `/api/method/helpdesk.search.search`

### Target Architecture (Based on Gameplan)
- **SQLite FTS**: Using Frappe Framework's `frappe.search.sqlite_search.SQLiteSearch`
- **Dedicated Search Page**: Full-featured search interface like Gameplan's Search.vue
- **Agent Portal Only**: Search functionality for agents only
- **Command Palette**: Simple navigation shortcuts, search redirects to dedicated page
- **Document Types**: HD Ticket, HD Ticket Comment, Communication
- **Advanced Filtering**: Team, status, priority, customer, date ranges

## Corrected Document Schema Analysis

### HD Ticket Fields (Verified)
- `name` (ticket ID)
- `subject` (ticket title)
- `description` (ticket content)
- `agent_group` (team field - NOT "team")
- `status` (ticket status)
- `priority` (ticket priority)
- `raised_by` (customer email)
- `owner` (ticket creator)
- `modified` (last modified date)

### HD Ticket Comment Fields (Verified)
- `name` (comment ID)
- `content` (comment text)
- `reference_ticket` (linked ticket - NOT "reference_name")
- `commented_by` (comment author)
- `modified` (comment date)

### Communication Fields (Verified)
- `name` (communication ID)
- `subject` (email subject)
- `content` (email content)
- `reference_doctype` (always "HD Ticket")
- `reference_name` (ticket ID)
- `sender` (email sender)
- `modified` (communication date)

## Implementation Plan

### Phase 1: Backend SQLite Search Implementation

#### 1.1 Create SQLite Search Class
**File**: `helpdesk/helpdesk/search_sqlite.py`

```python
class HelpdeskSearch(SQLiteSearch):
    INDEX_NAME = "helpdesk_search.db"

    INDEX_SCHEMA = {
        "metadata_fields": ["agent_group", "customer", "status", "priority", "owner", "reference_doctype", "reference_name", "reference_ticket"],
        "tokenizer": "unicode61 remove_diacritics 2 tokenchars '-_'",
    }

    INDEXABLE_DOCTYPES = {
        "HD Ticket": {
            "fields": ["name", "subject", {"content": "description"}, "modified", "agent_group", "status", "priority", "raised_by", "owner"],
        },
        "HD Ticket Comment": {
            "fields": ["name", "content", "modified", "reference_ticket", "commented_by", "owner"],
        },
        "Communication": {
            "fields": ["name", "subject", "content", "modified", "reference_doctype", "reference_name", "sender", "owner"],
            "filters": {"reference_doctype": "HD Ticket"},
        },
    }

    def get_search_filters(self):
        """Return permission filters based on accessible tickets."""
        accessible_tickets = self._get_accessible_tickets()

        if not accessible_tickets:
            return {"name": []}  # No accessible tickets

        return {"reference_ticket": accessible_tickets, "reference_name": accessible_tickets, "name": accessible_tickets}

    def _get_accessible_tickets(self):
        """Get tickets accessible to current user based on helpdesk permissions."""
        from helpdesk.utils import is_agent

        user = frappe.session.user

        if user == "Administrator":
            return frappe.get_all("HD Ticket", pluck="name")

        if is_agent(user):
            # Agent can see tickets in their teams + assigned tickets
            agent_teams = frappe.get_all("HD Team Member",
                filters={"user": user}, pluck="parent")

            assigned_tickets = []
            if frappe.db.exists("HD Ticket", {"_assign": ("like", f"%{user}%")}):
                assigned_tickets = frappe.get_all("HD Ticket",
                    filters={"_assign": ("like", f"%{user}%")}, pluck="name")

            team_tickets = []
            if agent_teams:
                team_tickets = frappe.get_all("HD Ticket",
                    filters={"agent_group": ("in", agent_teams)}, pluck="name")

            return list(set(assigned_tickets + team_tickets))

        # Non-agents have no search access
        return []

    def prepare_document(self, doc):
        """Prepare a document for indexing with helpdesk-specific handling."""
        document = super().prepare_document(doc)
        if not document:
            return None

        if doc.doctype == "HD Ticket Comment":
            # For comments, resolve the ticket for permissions
            document["reference_ticket"] = doc.reference_ticket

        if doc.doctype == "Communication":
            # For communications, ensure reference fields are set
            document["reference_doctype"] = doc.reference_doctype
            document["reference_name"] = doc.reference_name

        return document
```

#### 1.2 Permission Integration with Existing System
- Integrate with `helpdesk.utils.is_agent()` function
- Use existing HD Team Member relationships
- Respect ticket assignment (`_assign` field)
- Handle customer identification via `raised_by` field

### Phase 2: API Endpoints

#### 2.1 Main Search API
**File**: `helpdesk/api/search.py`

```python
import json
import frappe
from frappe import _

@frappe.whitelist()
def search(query, filters=None, limit=20, title_only=False):
    """Main search endpoint for the dedicated search page"""
    # Input validation
    if not query or len(query.strip()) < 2:
        frappe.throw(_("Search query must be at least 2 characters"))

    # Validate and parse limit
    try:
        limit = min(int(limit or 20), 100)  # Max 100 results
    except (ValueError, TypeError):
        limit = 20

    # Parse filters safely
    if isinstance(filters, str):
        try:
            filters = json.loads(filters) if filters else {}
        except json.JSONDecodeError:
            filters = {}

    from helpdesk.search_sqlite import HelpdeskSearch, HelpdeskSearchIndexMissingError

    search = HelpdeskSearch()

    try:
        result = search.search(query, filters=filters, limit=limit, title_only=title_only)
        return result
    except HelpdeskSearchIndexMissingError:
        frappe.throw(_("Search index not available. Please contact administrator."))

@frappe.whitelist()
def get_filter_options():
    """Get available filter options for search interface"""
    from helpdesk.search_sqlite import HelpdeskSearch

    search = HelpdeskSearch()

    if not search.index_exists():
        return {"teams": {}, "statuses": {}, "priorities": {}, "customers": {}, "doctypes": {}}

    return search.get_filter_options()

@frappe.whitelist()
def rebuild_index():
    """Rebuild search index - admin only"""
    if not frappe.has_permission("HD Settings", "write"):
        frappe.throw(_("Insufficient permissions"))

    from helpdesk.search_sqlite import build_index
    frappe.enqueue(build_index, queue="long")

    return {"message": "Search index rebuild started"}
```

#### 2.2 Command Palette Integration
**File**: `helpdesk/api/command_palette.py`

```python
@frappe.whitelist()
def search_quick(query):
    """Quick search for command palette - returns limited results"""
    if not query or len(query.strip()) < 2:
        return []

    from helpdesk.search_sqlite import HelpdeskSearch, HelpdeskSearchIndexMissingError
    from helpdesk.utils import is_agent

    search = HelpdeskSearch()

    try:
        result = search.search(query, title_only=True, limit=5)
    except HelpdeskSearchIndexMissingError:
        return []

    # Format for command palette
    items = []
    for r in result.get("results", []):
        if r["doctype"] == "HD Ticket":
            route_name = "TicketAgent" if is_agent() else "TicketCustomer"
            items.append({
                "title": r["title"],
                "doctype": "HD Ticket",
                "name": r["name"],
                "route": {
                    "name": route_name,
                    "params": {"ticketId": r["name"]}
                }
            })

    groups = []
    if items:
        groups.append({"title": "Tickets", "items": items})

    # Add "Search for..." option
    if query.strip() and is_agent():
        groups.append({
            "title": "Search",
            "items": [{
                "title": f'Search for "{query}"',
                "doctype": "Search",
                "name": "full-search",
                "route": {
                    "name": "SearchAgent",
                    "query": {"q": query}
                }
            }]
        })

    return groups
```

### Phase 3: Frontend Implementation

#### 3.1 Dedicated Search Page
**File**: `helpdesk/desk/src/pages/SearchAgent.vue`

```vue
<template>
  <div>
    <div>
      <header class="sticky top-0 z-10 border-b bg-surface-white px-4 py-2.5 sm:px-5">
        <div class="flex items-center justify-between">
          <Breadcrumbs :items="[{ label: 'Search', route: { name: 'SearchAgent' } }]" />
        </div>
      </header>
      <div class="mx-auto mt-6 max-w-4xl px-4 sm:px-5">
        <div class="flex items-center space-x-2 px-2.5">
          <TextInput
            ref="searchInput"
            class="flex-1"
            placeholder="Search or press / to focus"
            autocomplete="off"
            v-focus
            :model-value="query"
            @update:model-value="updateQuery"
            @keydown="newSearch = true"
            @keydown.enter="() => submit()"
          >
            <template #prefix>
              <LucideSearch class="w-4 text-ink-gray-5" />
            </template>
            <template #suffix>
              <div class="flex items-center">
                <button
                  v-if="query"
                  @click="clearSearch"
                  class="p-1 size-6 grid place-content-center focus:outline-none focus:ring focus:ring-outline-gray-3 rounded"
                >
                  <LucideX class="w-4 text-ink-gray-7" />
                </button>
              </div>
            </template>
          </TextInput>
        </div>

        <!-- Filter Panel -->
        <div class="mt-2 px-2.5">
          <div class="flex gap-2 items-center">
            <!-- Team Filter -->
            <MultiSelect
              :options="teamsFilterOptions"
              :model-value="activeFilters.agent_group || []"
              @update:model-value="(values) => updateFilter('agent_group', values)"
              placeholder="Team"
              label="Team"
            />

            <!-- Status Filter -->
            <MultiSelect
              :options="statusFilterOptions"
              :model-value="activeFilters.status || []"
              @update:model-value="(values) => updateFilter('status', values)"
              placeholder="Status"
              label="Status"
            />

            <!-- Priority Filter -->
            <MultiSelect
              :options="priorityFilterOptions"
              :model-value="activeFilters.priority || []"
              @update:model-value="(values) => updateFilter('priority', values)"
              placeholder="Priority"
              label="Priority"
            />

            <!-- Document Type Filter -->
            <MultiSelect
              :options="doctypesFilterOptions"
              :model-value="activeFilters.doctype || []"
              @update:model-value="(values) => updateFilter('doctype', values)"
              placeholder="Type"
              label="Type"
            />
          </div>
        </div>

        <!-- Search Summary -->
        <div class="mt-2 px-2.5 text-sm flex items-center justify-between min-h-6">
          <div>
            <template v-if="search.error">
              <ErrorMessage
                :message="
                  search.error.type == 'HelpdeskSearchIndexMissingError'
                    ? 'Search index does not exist. Please build the index first.'
                    : search.error
                "
              />
            </template>
            <template v-else-if="newSearch && query.length > 2">
              <p class="text-ink-gray-6">Press enter to search</p>
            </template>
            <template v-else-if="search.loading">
              <p class="text-ink-gray-6">Searching...</p>
            </template>
            <template v-else-if="searchResponse?.summary">
              <div class="space-y-1">
                <p class="text-ink-gray-6">
                  {{ searchResponse.summary.filtered_matches }} matches ({{
                    searchResponse.summary.duration
                  }}s)
                  <span v-if="hasActiveFilters()">
                    •
                    {{ Object.keys(searchResponse.summary.applied_filters || {}).length }} filter(s)
                    applied
                  </span>
                </p>
                <p v-if="searchResponse.summary.corrected_query" class="text-ink-gray-6">
                  <span class="text-ink-gray-5">Searched for:</span>
                  <span class="ml-1 font-medium text-primary">
                    {{ searchResponse.summary.corrected_query }}
                  </span>
                </p>
              </div>
            </template>
          </div>

          <!-- Inline Feedback Section -->
          <div
            v-if="searchResponse?.results?.length && !feedbackGiven"
            class="flex items-center gap-2"
          >
            <span class="text-ink-gray-6">Helpful?</span>
            <div class="flex items-center gap-1">
              <Tooltip text="Yes, results were helpful">
                <button
                  @click="submitFeedback(true)"
                  class="p-1 hover:bg-surface-gray-2 rounded-full transition-colors"
                >
                  <LucideThumbsUp class="size-4 text-ink-gray-7" />
                </button>
              </Tooltip>
              <Tooltip text="No, results were not helpful">
                <button
                  @click="submitFeedback(false)"
                  class="p-1 hover:bg-surface-gray-2 rounded-full transition-colors"
                >
                  <LucideThumbsDown class="size-4 text-ink-gray-7" />
                </button>
              </Tooltip>
            </div>
          </div>
          <div v-else-if="feedbackGiven" class="text-ink-gray-6">Thanks for your feedback!</div>
        </div>

        <div class="mt-5">
          <template v-for="item in searchResponse?.results" :key="item.id">
            <router-link
              :to="getItemRoute(item)"
              class="flex space-x-2 overflow-hidden rounded px-2.5 py-3 hover:bg-surface-gray-2"
            >
              <div>
                <UserAvatar :name="item.raised_by || item.author || 'System'" />
              </div>
              <div class="w-full">
                <div class="flex items-center">
                  <div v-if="item.title" class="text-base font-medium" v-html="item.title" />
                  <div class="text-base font-medium" v-else>
                    {{ item.name }}
                  </div>
                  <span class="px-1 leading-none text-sm text-ink-gray-5">
                    &middot; {{ item.doctype.replace('HD ', '') }}
                  </span>
                  <div class="ml-auto text-sm text-ink-gray-5">
                    {{ formatDate(item.modified) }}
                  </div>
                </div>
                <div
                  v-if="item.content"
                  class="mt-1 text-p-base text-ink-gray-6"
                  v-html="item.content"
                ></div>
              </div>
            </router-link>
            <div class="border-b mx-2"></div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, useTemplateRef } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Breadcrumbs, TextInput, debounce, Tooltip, ErrorMessage } from 'frappe-ui'
import { createResource } from 'frappe-ui'
import UserAvatar from '@/components/UserAvatar.vue'
import MultiSelect from '@/components/MultiSelect.vue'
import { vFocus } from '@/directives'

// Icons
import LucideSearch from '~icons/lucide/search'
import LucideX from '~icons/lucide/x'
import LucideThumbsUp from '~icons/lucide/thumbs-up'
import LucideThumbsDown from '~icons/lucide/thumbs-down'

// Type Definitions
interface SearchSummary {
  duration: number
  total_matches: number
  returned_matches: number
  filtered_matches: number
  corrected_words?: Record<string, string>
  corrected_query?: string
  applied_filters?: SearchFilters
}

interface SearchResultItem {
  id: string
  title: string
  content: string
  preview: string
  doctype: string
  name: string
  agent_group?: string
  status?: string
  priority?: string
  reference_ticket?: string
  reference_name?: string
  modified: number | string
  author?: string
  raised_by?: string
  score: number
}

interface SearchResponse {
  results: SearchResultItem[]
  summary: SearchSummary
}

interface SearchFilters {
  agent_group?: string[]
  status?: string[]
  priority?: string[]
  doctype?: string[]
}

interface FilterOption {
  value: string
  label: string
  count?: number
}

interface FilterOptions {
  teams: Record<string, number>
  statuses: Record<string, number>
  priorities: Record<string, number>
  doctypes: Record<string, number>
}

// Reactive State
const query = ref('')
const searchResponse = ref<SearchResponse | null>(null)
const newSearch = ref(true)
const feedbackGiven = ref(false)
const activeFilters = ref<SearchFilters>({})

// Template Refs
const searchInput = useTemplateRef<typeof TextInput>('searchInput')

// Composables and External Data
const router = useRouter()
const route = useRoute()

// API Calls Setup
const search = createResource({
  url: 'helpdesk.api.search.search',
  makeParams() {
    return {
      query: query.value,
      filters: JSON.stringify(activeFilters.value),
      limit: 50
    }
  },
  onSuccess(response) {
    searchResponse.value = response
    newSearch.value = false
  },
})

const filterOptions = createResource({
  url: 'helpdesk.api.search.get_filter_options',
  auto: true,
})

// Filter Options Computed Properties
const teamsFilterOptions = computed(() => {
  const options = filterOptions.data?.teams || {}
  return Object.entries(options).map(([value, count]) => ({
    value,
    label: `${value} (${count})`,
    count
  }))
})

const statusFilterOptions = computed(() => {
  const options = filterOptions.data?.statuses || {}
  return Object.entries(options).map(([value, count]) => ({
    value,
    label: `${value} (${count})`,
    count
  }))
})

const priorityFilterOptions = computed(() => {
  const options = filterOptions.data?.priorities || {}
  return Object.entries(options).map(([value, count]) => ({
    value,
    label: `${value} (${count})`,
    count
  }))
})

const doctypesFilterOptions = computed(() => {
  return [
    { value: 'HD Ticket', label: 'Tickets', count: 0 },
    { value: 'HD Ticket Comment', label: 'Comments', count: 0 },
    { value: 'Communication', label: 'Communications', count: 0 }
  ]
})

// Search Functions
const debouncedSubmit = debounce(() => {
  if (query.value.length > 2) {
    search.submit()
  }
}, 500)

function updateQuery(value: string) {
  query.value = value
  newSearch.value = true
  debouncedSubmit()
}

function submit() {
  if (query.value.length > 2) {
    search.submit()
  }
}

function clearSearch() {
  query.value = ''
  searchResponse.value = null
  newSearch.value = true
}

function hasActiveFilters() {
  return Object.values(activeFilters.value).some(filter => filter && filter.length > 0)
}

function updateFilter(key: keyof SearchFilters, values: string[]) {
  activeFilters.value[key] = values
  if (query.value.length > 2) {
    debouncedSubmit()
  }
}

function getItemRoute(item: SearchResultItem) {
  if (!item || !item.doctype || !item.name) {
    return { name: 'SearchAgent' }
  }

  if (item.doctype === 'HD Ticket') {
    return {
      name: 'TicketAgent',
      params: { ticketId: item.name }
    }
  } else if (item.doctype === 'HD Ticket Comment' && item.reference_ticket) {
    return {
      name: 'TicketAgent',
      params: { ticketId: item.reference_ticket },
      hash: `#comment-${item.name}`
    }
  } else if (item.doctype === 'Communication' && item.reference_name) {
    return {
      name: 'TicketAgent',
      params: { ticketId: item.reference_name },
      hash: `#communication-${item.name}`
    }
  }
  return { name: 'SearchAgent' }
}

function submitFeedback(helpful: boolean) {
  // TODO: Implement feedback submission
  feedbackGiven.value = true
}

function formatDate(date: number | string) {
  if (!date) return ''
  try {
    const dateObj = typeof date === 'number' ? new Date(date * 1000) : new Date(date)
    return dateObj.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return ''
  }
}

// Lifecycle
onMounted(() => {
  if (route.query.q && typeof route.query.q === 'string') {
    query.value = route.query.q
    submit()
  }
})
</script>
```

#### 3.2 Updated Command Palette
**File**: `helpdesk/desk/src/components/command-palette/CommandPalette.vue`

```vue
<template>
  <Dialog v-model="show" :options="{ size: 'xl', position: 'top' }">
    <template #body>
      <div>
        <Combobox nullable @update:model-value="onSelection">
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center">
              <LucideSearch class="h-4 w-4 text-ink-gray-5" />
            </div>
            <ComboboxInput
              placeholder="Search or navigate..."
              class="w-full border-none bg-transparent py-3 pl-11 pr-4 text-base text-ink-gray-9 placeholder-ink-gray-5 focus:ring-0"
              autocomplete="off"
              @input="onInput"
            />
          </div>
          <ComboboxOptions
            class="max-h-96 overflow-auto border-t border-outline-gray-1"
            static
            :hold="true"
          >
            <div v-for="group in groupedResults" :key="group.title" class="mt-4 first:mt-3">
              <div v-if="!group.hideTitle" class="px-4 mb-2 text-sm font-medium text-ink-gray-6">
                {{ group.title }}
              </div>
              <ComboboxOption
                v-for="item in group.items"
                :key="`${item.doctype}:${item.name}`"
                v-slot="{ active }"
                :value="item"
                class="px-2"
              >
                <div
                  class="flex items-center rounded px-2 py-2 text-base"
                  :class="{ 'bg-surface-gray-2': active }"
                >
                  <component :is="item.icon" v-if="item.icon" class="mr-3 h-4 w-4 text-ink-gray-6" />
                  <span class="flex-1 truncate">{{ item.title }}</span>
                  <span v-if="item.name && item.name !== 'full-search'" class="ml-2 text-sm text-ink-gray-5">
                    #{{ item.name }}
                  </span>
                </div>
              </ComboboxOption>
            </div>
          </ComboboxOptions>
        </Combobox>
      </div>
    </template>
  </Dialog>
</template>

<script>
import { h, ref } from 'vue'
import { Combobox, ComboboxInput, ComboboxOptions, ComboboxOption } from '@headlessui/vue'
import { createResource } from 'frappe-ui'
import LucideSearch from '~icons/lucide/search'
import LucideTicket from '~icons/lucide/ticket'
import LucideBookOpen from '~icons/lucide/book-open'
import LucideUsers from '~icons/lucide/users'

let show = ref(false)

export function showCommandPalette() {
  show.value = true
}

export function hideCommandPalette() {
  show.value = false
}

export function toggleCommandPalette() {
  show.value = !show.value
}

export default {
  name: 'CommandPalette',
  components: {
    Combobox,
    ComboboxInput,
    ComboboxOptions,
    ComboboxOption,
  },
  setup() {
    return { show }
  },
  data() {
    return {
      query: '',
    }
  },
  resources: {
    quickSearch() {
      return {
        url: 'helpdesk.api.command_palette.search_quick',
        makeParams(query) {
          return { query }
        },
        debounce: 300,
      }
    },
  },
  computed: {
    navigationItems() {
      return {
        title: 'Navigate',
        items: [
          {
            title: 'Tickets',
            icon: () => h(LucideTicket),
            route: { name: 'TicketsAgent' },
          },
          {
            title: 'Knowledge Base',
            icon: () => h(LucideBookOpen),
            route: { name: 'AgentKnowledgeBase' },
          },
          {
            title: 'Agents',
            icon: () => h(LucideUsers),
            route: { name: 'AgentList' },
          },
        ],
      }
    },
    groupedResults() {
      let results = []

      // Show search results if query exists
      if (this.query.length > 2 && this.$resources.quickSearch.data) {
        results = this.$resources.quickSearch.data
      }

      // Always show navigation items if no specific results
      if (results.length === 0) {
        results = [this.navigationItems]
      }

      return results
    },
  },
  watch: {
    show(value) {
      if (value) {
        this.query = ''
      }
    },
  },
  mounted() {
    this.addKeyboardShortcut()
  },
  methods: {
    onInput(e) {
      this.query = e.target.value
      if (this.query && this.query.length > 2) {
        this.$resources.quickSearch.submit(this.query)
      }
    },
    onSelection(value) {
      if (value?.route) {
        this.$router.push(value.route)
        hideCommandPalette()
      }
    },
    addKeyboardShortcut() {
      window.addEventListener('keydown', (e) => {
        if (
          e.key === 'k' &&
          (e.ctrlKey || e.metaKey) &&
          !e.target.classList?.contains('ProseMirror')
        ) {
          toggleCommandPalette()
          e.preventDefault()
        }
      })
    },
  },
}
</script>
```

### Phase 4: Integration Points

#### 4.1 Routing Updates
**File**: `helpdesk/desk/src/router/index.ts`

Add search route:

```typescript
// Agent Portal Search
{
  path: '/search',
  name: 'SearchAgent',
  component: () => import('@/pages/SearchAgent.vue'),
  meta: { auth: true, agent: true }
}
```

#### 4.2 Hooks Integration
**File**: `helpdesk/helpdesk/hooks.py`

```python
after_migrate = [
    "helpdesk.search_sqlite.build_index_in_background",
    "helpdesk.search.build_index_in_background",  # Keep existing for migration
]

scheduler_events = {
    "all": [
        "helpdesk.search_sqlite.build_index_if_not_exists",
        "helpdesk.search.build_index_if_not_exists",  # Keep existing
    ],
}

doc_events = {
    "HD Ticket": {
        "after_insert": [
            "helpdesk.search.index_doc",  # Existing Redis search
            "helpdesk.search_sqlite.update_doc_index",  # New SQLite search
        ],
        "on_update": [
            "helpdesk.search.index_doc",
            "helpdesk.search_sqlite.update_doc_index",
        ],
        "on_trash": [
            "helpdesk.search.remove_doc",
            "helpdesk.search_sqlite.delete_doc_index",
        ],
    },
    "HD Ticket Comment": {
        "after_insert": ["helpdesk.search_sqlite.update_doc_index"],
        "on_update": ["helpdesk.search_sqlite.update_doc_index"],
        "on_trash": ["helpdesk.search_sqlite.delete_doc_index"],
    },
    "Communication": {
        "after_insert": ["helpdesk.search_sqlite.update_doc_index"],
        "on_update": ["helpdesk.search_sqlite.update_doc_index"],
        "on_trash": ["helpdesk.search_sqlite.delete_doc_index"],
    },
}
```

### Phase 5: Migration Strategy

#### 5.1 Parallel Implementation
- Keep existing Redis search functional during development
- Add site config flag: `use_sqlite_search = 0/1`
- Gradual migration per site
- A/B testing capability

#### 5.2 Migration Utilities
**File**: `helpdesk/helpdesk/migration.py`

```python
@frappe.whitelist()
def migrate_to_sqlite_search():
    """Admin-only migration from Redis to SQLite search"""
    if not frappe.has_permission("HD Settings", "write"):
        frappe.throw("Insufficient permissions")

    # Build SQLite index
    from helpdesk.search_sqlite import build_index
    build_index()

    # Update site config
    frappe.db.set_single_value("HD Settings", "search_backend", "sqlite")

    return {"message": "Migration completed successfully"}

@frappe.whitelist()
def rollback_to_redis_search():
    """Rollback to Redis search if needed"""
    if not frappe.has_permission("HD Settings", "write"):
        frappe.throw("Insufficient permissions")

    frappe.db.set_single_value("HD Settings", "search_backend", "redis")

    return {"message": "Rollback completed successfully"}
```

## Implementation Todo List

### Frontend - MultiSelect Component
- [ ] Copy `gameplan/frontend/src/components/MultiSelect.vue` to `helpdesk/desk/src/components/MultiSelect.vue`
- [ ] Ensure MultiSelect component works with helpdesk's frappe-ui version
- [ ] Test MultiSelect with filter options data structure
- [ ] Add any helpdesk-specific styling adjustments if needed

### Backend - SQLite Search Foundation
- [ ] Create `helpdesk/helpdesk/search_sqlite.py` with corrected field names
- [ ] Implement `HelpdeskSearch` class extending `SQLiteSearch`
- [ ] Add `INDEX_SCHEMA` with correct metadata fields (agent_group, not team)
- [ ] Define `INDEXABLE_DOCTYPES` with verified field mappings
- [ ] Implement `prepare_document()` method for each doctype
- [ ] Add permission filtering using existing `helpdesk.utils.is_agent()`
- [ ] Implement `_get_accessible_tickets()` with HD Team Member integration
- [ ] Add `get_filter_options()` for search interface
- [ ] Create `HelpdeskSearchIndexMissingError` exception class
- [ ] Add `build_index()` and background building functions
- [ ] Add document update/delete handlers

### Backend - API Endpoints
- [ ] Create `helpdesk/api/search.py` with proper validation
- [ ] Implement `search()` endpoint with input sanitization
- [ ] Add `get_filter_options()` endpoint
- [ ] Add `rebuild_index()` admin endpoint
- [ ] Create `helpdesk/api/command_palette.py`
- [ ] Implement `search_quick()` for command palette
- [ ] Add proper error handling and rate limiting
- [ ] Include Frappe `@whitelist()` decorators

### Backend - Permission System
- [ ] Integrate with existing `is_agent()` function
- [ ] Query HD Team Member for agent team memberships
- [ ] Check `_assign` field for ticket assignments
- [ ] Block non-agent access to search functionality
- [ ] Add permission caching for performance
- [ ] Test edge cases (team transfers, reassignments)

### Backend - Migration & Hooks
- [ ] Update `helpdesk/helpdesk/hooks.py` with dual search support
- [ ] Add parallel indexing for both Redis and SQLite
- [ ] Create migration utilities in `helpdesk/helpdesk/migration.py`
- [ ] Add site config flag for search backend selection
- [ ] Implement rollback procedures

### Frontend - Search Page
- [ ] Create `helpdesk/desk/src/pages/SearchAgent.vue`
- [ ] Copy MultiSelect component from Gameplan to `helpdesk/desk/src/components/MultiSelect.vue`
- [ ] Implement search input with TextInput component from frappe-ui
- [ ] Add filter interface using MultiSelect components (agent_group, status, priority, doctype)
- [ ] Display search results with UserAvatar and exact Gameplan styling
- [ ] Add navigation to ticket details from results
- [ ] Handle empty states and loading states
- [ ] Add keyboard shortcuts and accessibility with vFocus directive
- [ ] Add agent permission checks
- [ ] Implement search feedback system with thumbs up/down
- [ ] Add proper error handling for search API failures
- [ ] Add TypeScript interfaces matching Gameplan's structure
- [ ] Add breadcrumbs component with proper navigation

### Frontend - Command Palette
- [ ] Update existing command palette with corrected API
- [ ] Remove detailed search results display
- [ ] Add quick search with top 5 results
- [ ] Include "Search for..." navigation option
- [ ] Maintain keyboard shortcuts and navigation

### Frontend - Routing & Integration
- [ ] Add search route to router for agent portal
- [ ] Add route guards to ensure only agents can access
- [ ] Update navigation menus with search links
- [ ] Handle deep linking with search query parameters
- [ ] Add keyboard shortcut (/) for search focus

### Testing & Quality Assurance
- [ ] Unit tests for search class with permission scenarios
- [ ] API endpoint testing with agent and non-agent roles
- [ ] Frontend component testing for search page
- [ ] E2E testing for complete search workflows
- [ ] Performance testing with large datasets
- [ ] Security testing for non-agent access attempts
- [ ] Accessibility testing for keyboard navigation
- [ ] Test breadcrumbs component error scenarios
- [ ] Test search with malformed API responses
- [ ] Test filter options with undefined/null values

### Documentation
- [ ] User guide for search functionality
- [ ] Admin guide for search management
- [ ] API documentation for search endpoints
- [ ] Migration guide from Redis to SQLite
- [ ] Troubleshooting guide for common issues

## Success Criteria

1. **Functionality**: Agent portal has fully working search functionality
2. **Performance**: Search results load within 300ms for typical queries
3. **Security**: Only authorized agents can access search functionality
4. **Usability**: Intuitive interface with keyboard shortcuts
5. **Migration**: Smooth transition from Redis without data loss
6. **Scalability**: Handles helpdesk installations with 100K+ tickets

## Conclusion

This corrected implementation plan addresses the critical issues identified in the review:

- **Fixed field names** to match actual helpdesk schema
- **Detailed permission system** integration with existing helpdesk functions
- **Proper API specifications** with validation and error handling
- **Agent-only focus** with proper permission enforcement
- **Migration strategy** that minimizes disruption
- **Comprehensive testing** plan covering security and performance

The plan is now ready for implementation by a coding agent, with clear technical specifications and actionable todo items focused on agent search functionality.
