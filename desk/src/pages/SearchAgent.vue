<template>
  <div>
    <div>
      <LayoutHeader>
        <template #left-header>
          <Breadcrumbs
            :items="[{ label: 'Search', route: { name: 'SearchAgent' } }]"
          />
        </template>
      </LayoutHeader>
      <div class="mx-auto mt-6 max-w-4xl px-4 sm:px-5">
        <div class="flex items-center space-x-2 px-2.5">
          <TextInput
            ref="searchInput"
            class="flex-1"
            placeholder="Search tickets, comments, and communications..."
            autocomplete="off"
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
            <SearchMultiSelect
              :options="teamsFilterOptions"
              :model-value="activeFilters.agent_group || []"
              @update:model-value="
                (values) => updateFilter('agent_group', values)
              "
              placeholder="Team"
              label="Team"
            />

            <!-- Status Filter -->
            <SearchMultiSelect
              :options="statusFilterOptions"
              :model-value="activeFilters.status || []"
              @update:model-value="(values) => updateFilter('status', values)"
              placeholder="Status"
              label="Status"
            />

            <!-- Priority Filter -->
            <SearchMultiSelect
              :options="priorityFilterOptions"
              :model-value="activeFilters.priority || []"
              @update:model-value="(values) => updateFilter('priority', values)"
              placeholder="Priority"
              label="Priority"
            />

            <!-- Document Type Filter -->
            <SearchMultiSelect
              :options="doctypesFilterOptions"
              :model-value="activeFilters.doctype || []"
              @update:model-value="(values) => updateFilter('doctype', values)"
              placeholder="Type"
              label="Type"
            />
            <Button
              v-if="hasActiveFilters()"
              size="sm"
              class="ml-auto text-ink-gray-5"
              variant="gray-ghost"
              @click="clearFilters"
              label="Clear all filters"
            />
          </div>
        </div>

        <!-- Search Summary -->
        <div
          class="mt-2 px-2.5 text-sm flex items-center justify-between min-h-6"
        >
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
                    {{
                      Object.keys(searchResponse.summary.applied_filters || {})
                        .length
                    }}
                    filter(s) applied
                  </span>
                </p>
                <p
                  v-if="searchResponse.summary.corrected_query"
                  class="text-ink-gray-6"
                >
                  <span class="text-ink-gray-5">Searched for:</span>
                  <span class="ml-1 font-medium text-primary">
                    {{ searchResponse.summary.corrected_query }}
                  </span>
                </p>
              </div>
            </template>
          </div>
        </div>

        <div class="mt-5">
          <template v-for="item in searchResponse?.results" :key="item.id">
            <router-link
              :to="getItemRoute(item)"
              class="flex space-x-2 overflow-hidden rounded px-2.5 py-3 hover:bg-surface-gray-2"
            >
              <div class="flex items-start space-x-2">
                <div class="flex-shrink-0">
                  <LucideTicket
                    v-if="item.doctype === 'HD Ticket'"
                    class="h-4 w-4 text-ink-gray-6"
                  />
                  <LucideMessageSquare
                    v-else-if="item.doctype === 'HD Ticket Comment'"
                    class="h-4 w-4 text-ink-gray-6"
                  />
                  <LucideMail
                    v-else-if="item.doctype === 'Communication'"
                    class="h-4 w-4 text-ink-gray-6"
                  />
                </div>
                <!-- <UserAvatar :name="item.raised_by || item.author || 'System'" /> -->
              </div>
              <div class="w-full">
                <div class="flex items-center">
                  <div
                    v-if="item.title"
                    class="text-base font-medium"
                    v-html="item.title"
                  />
                  <div class="text-base font-medium" v-else>
                    {{ item.name }}
                  </div>
                  <span class="px-1 leading-none text-sm text-ink-gray-5">
                    &middot;
                    {{
                      item.doctype == "Communication"
                        ? "Email"
                        : item.doctype.replace("HD ", "")
                    }}
                  </span>
                  <span class="px-1 leading-none text-sm text-ink-gray-5">
                    &middot; #{{ getTicketNumber(item) }}
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
import { LayoutHeader } from "@/components";
import SearchMultiSelect from "@/components/SearchMultiSelect.vue";
import dayjs from "dayjs";
import {
  Breadcrumbs,
  createResource,
  debounce,
  ErrorMessage,
  TextInput,
} from "frappe-ui";
import { computed, nextTick, onMounted, ref, useTemplateRef, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

// Icons

// Type Definitions
interface SearchSummary {
  duration: number;
  total_matches: number;
  returned_matches: number;
  filtered_matches: number;
  corrected_words?: Record<string, string>;
  corrected_query?: string;
  applied_filters?: SearchFilters;
}

interface SearchResultItem {
  id: string;
  title: string;
  content: string;
  preview: string;
  doctype: string;
  name: string;
  agent_group?: string;
  status?: string;
  priority?: string;
  reference_ticket?: string;
  reference_name?: string;
  modified: number | string;
  author?: string;
  raised_by?: string;
  score: number;
}

interface SearchResponse {
  results: SearchResultItem[];
  summary: SearchSummary;
}

interface SearchFilters {
  agent_group?: string[];
  status?: string[];
  priority?: string[];
  doctype?: string[];
}

interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

interface FilterOptions {
  teams: Record<string, number>;
  statuses: Record<string, number>;
  priorities: Record<string, number>;
  doctypes: Record<string, number>;
}

// Constants and Configuration
const STORAGE_KEY_PREFIX = "helpdesk_search:";

// Reactive State
const query = ref("");
const searchResponse = ref<SearchResponse | null>(null);
const newSearch = ref(true);
const activeFilters = ref<SearchFilters>({});

// Template Refs
const searchInput = useTemplateRef<typeof TextInput>("searchInput");

// Composables and External Data
const router = useRouter();
const route = useRoute();

// API Calls Setup
const search = createResource({
  url: "helpdesk.api.search.search",
  makeParams() {
    return {
      query: query.value,
      filters: JSON.stringify(activeFilters.value),
      limit: 50,
    };
  },
  onSuccess(response) {
    searchResponse.value = response;
    newSearch.value = false;
    if (query.value) {
      saveSearchState(query.value, response);
    }
  },
});

const filterOptions = createResource({
  url: "helpdesk.api.search.get_filter_options",
  auto: true,
});

// Filter Options Computed Properties
const teamsFilterOptions = computed(() => {
  const options = filterOptions.data?.teams || {};
  return Object.entries(options).map(([value]) => ({
    value,
    label: `${value}`,
    // count,
  }));
});

const statusFilterOptions = computed(() => {
  const options = filterOptions.data?.statuses || {};
  return Object.entries(options).map(([value]) => ({
    value,
    label: `${value}`,
    // count,
  }));
});

const priorityFilterOptions = computed(() => {
  const options = filterOptions.data?.priorities || {};
  return Object.entries(options).map(([value]) => ({
    value,
    label: `${value}`,
    // count,
  }));
});

const doctypesFilterOptions = computed(() => {
  return [
    { value: "HD Ticket", label: "Tickets", count: 0 },
    { value: "Communication", label: "Emails", count: 0 },
    { value: "HD Ticket Comment", label: "Comments", count: 0 },
  ];
});

// Search Functions
const debouncedSubmit = debounce(() => {
  if (query.value.length > 2) {
    search.submit();
  }
}, 500);

function updateQuery(value: string) {
  query.value = value;
  newSearch.value = true;
  debouncedSubmit();
}

function submit() {
  if (query.value.length > 2) {
    // Update the URL query parameter
    router.replace({ name: "SearchAgent", query: { q: query.value } });
    search.submit();
  }
}

function clearSearch() {
  query.value = "";
  searchResponse.value = null;
  newSearch.value = true;
  clearStoredSearches();
  // Clear the URL query parameter
  router.replace({ name: "SearchAgent" });
}

function clearFilters() {
  activeFilters.value = {};
  if (query.value.length > 2) {
    debouncedSubmit();
  }
}

function hasActiveFilters() {
  return Object.values(activeFilters.value).some(
    (filter) => filter && filter.length > 0
  );
}

function updateFilter(key: keyof SearchFilters, values: string[]) {
  if (!values || values.length === 0) {
    delete activeFilters.value[key];
  } else {
    activeFilters.value[key] = values;
  }

  if (query.value.length > 2) {
    debouncedSubmit();
  }
}

function getItemRoute(item: SearchResultItem) {
  if (!item || !item.doctype || !item.name) {
    return { name: "SearchAgent" };
  }

  if (item.doctype === "HD Ticket") {
    return {
      name: "TicketAgent",
      params: { ticketId: item.name },
    };
  } else if (item.doctype === "HD Ticket Comment" && item.reference_ticket) {
    return {
      name: "TicketAgent",
      params: { ticketId: item.reference_ticket },
      hash: `#comment-${item.name}`,
    };
  } else if (item.doctype === "Communication" && item.reference_name) {
    return {
      name: "TicketAgent",
      params: { ticketId: item.reference_name },
      hash: `#communication-${item.name}`,
    };
  }
  return { name: "SearchAgent" };
}

function getTicketNumber(item: SearchResultItem) {
  if (!item || !item.doctype) {
    return "";
  }

  if (item.doctype === "HD Ticket") {
    return item.name || "";
  } else if (item.doctype === "HD Ticket Comment") {
    return item.reference_ticket || "";
  } else if (item.doctype === "Communication") {
    return item.reference_name || "";
  }
  return "";
}

function formatDate(date: number | string) {
  if (!date) return "";
  let FORMAT = "MMM D, YYYY hh:mm A";
  try {
    // Handle Unix timestamp (seconds) - use dayjs.unix()
    if (typeof date === "number") {
      return dayjs.unix(date).format(FORMAT);
    }
    // Handle string dates
    return dayjs(date).format(FORMAT);
  } catch (error) {
    return "";
  }
}

// Search State Persistence
function getStorageKey(query: string) {
  return `${STORAGE_KEY_PREFIX}${query}`;
}

function loadSearchState(searchQuery: string) {
  const saved = localStorage.getItem(getStorageKey(searchQuery));
  if (saved) {
    const state = JSON.parse(saved);
    // Check if stored result is less than 30 minutes old
    if (Date.now() - state.timestamp < 30 * 60 * 1000) {
      searchResponse.value = state.results;
      // Restore active filters if they exist
      if (state.filters) {
        activeFilters.value = state.filters;
      }
      newSearch.value = false;
      return true;
    }
    // Remove expired results
    localStorage.removeItem(getStorageKey(searchQuery));
  }
  return false;
}

function saveSearchState(searchQuery: string, results: SearchResponse) {
  const state = {
    results,
    filters: activeFilters.value,
    timestamp: Date.now(),
  };
  localStorage.setItem(getStorageKey(searchQuery), JSON.stringify(state));
}

function clearStoredSearches() {
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith(STORAGE_KEY_PREFIX)) {
      localStorage.removeItem(key);
    }
  }
}

// Watch for route query changes (browser back/forward navigation)
watch(
  () => route.query.q,
  (newQuery) => {
    if (newQuery && typeof newQuery === "string" && newQuery !== query.value) {
      query.value = newQuery;
      newSearch.value = false; // Prevent showing "Press enter to search"
      search.submit();
    } else if (!newQuery && query.value) {
      query.value = "";
      searchResponse.value = null;
      newSearch.value = true;
    }
  }
);

function addFocusShortcut() {
  nextTick(() => {
    window.addEventListener("keydown", (e) => {
      if (e.key === "/") {
        e.preventDefault();
        searchInput.value.el.focus();
      }
    });
  });
}

// Lifecycle
onMounted(() => {
  const searchQuery = route.query.q as string;
  if (searchQuery) {
    query.value = searchQuery;
    if (!loadSearchState(searchQuery)) {
      submit();
    }
  } else {
    clearStoredSearches();
  }
  // add a shortcut when presses "/" focus on this element
  addFocusShortcut();
});
</script>
