<template>
  <div class="canned-response-selector">
    <Popover placement="top-start">
      <template #target="{ togglePopover }">
        <Button
          theme="gray"
          variant="ghost"
          @click="togglePopover()"
          :title="__('Insert Canned Response')"
        >
          <template #icon>
            <FeatherIcon name="message-square" class="h-4" />
          </template>
        </Button>
      </template>
      <template #body>
        <div class="p-2 w-96 max-h-96 overflow-y-auto">
          <div class="mb-3">
            <input
              v-model="searchTerm"
              type="text"
              :placeholder="__('Search canned responses...')"
              class="form-input w-full text-sm"
              @input="filterResponses"
            />
          </div>

          <div v-if="categoryFilter" class="mb-2">
            <div class="flex flex-wrap gap-1">
              <Badge
                v-for="category in categories"
                :key="category"
                :label="category"
                :variant="categoryFilter === category ? 'solid' : 'subtle'"
                class="cursor-pointer"
                @click="setCategoryFilter(category)"
              />
              <Badge
                label="All"
                :variant="!categoryFilter ? 'solid' : 'subtle'"
                class="cursor-pointer"
                @click="setCategoryFilter(null)"
              />
            </div>
          </div>

          <div v-if="loading" class="text-center py-4">
            <LoadingIndicator />
          </div>

          <div v-else-if="filteredResponses.length === 0" class="text-center py-4 text-gray-500">
            {{ __('No canned responses found') }}
          </div>

          <div v-else class="space-y-1">
            <div
              v-for="response in filteredResponses"
              :key="response.name"
              class="p-2 hover:bg-gray-100 rounded cursor-pointer"
              @click="selectResponse(response)"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="font-medium text-sm">{{ response.title }}</div>
                  <div
                    v-if="response.shortcut"
                    class="text-xs text-gray-500 mt-0.5"
                  >
                    {{ response.shortcut }}
                  </div>
                  <div
                    class="text-xs text-gray-600 mt-1 line-clamp-2"
                    v-html="stripHtml(response.message)"
                  ></div>
                </div>
                <Badge
                  v-if="response.category"
                  :label="response.category"
                  variant="subtle"
                  class="ml-2"
                />
              </div>
              <div
                v-if="response.usage_count > 0"
                class="text-xs text-gray-400 mt-1"
              >
                {{ __('Used {0} times', [response.usage_count]) }}
              </div>
            </div>
          </div>

          <div class="mt-3 pt-3 border-t">
            <router-link
              to="/helpdesk/canned-responses"
              class="text-sm text-blue-600 hover:text-blue-700"
            >
              {{ __('Manage Canned Responses') }}
            </router-link>
          </div>
        </div>
      </template>
    </Popover>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Popover, Badge, createResource } from 'frappe-ui';

const props = defineProps({
  onSelect: {
    type: Function,
    required: true,
  },
});

const searchTerm = ref('');
const categoryFilter = ref(null);
const loading = ref(false);
const responses = ref([]);

const categories = [
  'Greeting',
  'Closing',
  'Troubleshooting',
  'Billing',
  'Account',
  'General',
  'Escalation',
  'Follow-up',
];

const cannedResponsesResource = createResource({
  url: 'helpdesk.helpdesk.doctype.hd_canned_response.hd_canned_response.get_canned_responses',
  auto: true,
  onSuccess: (data) => {
    responses.value = data;
    loading.value = false;
  },
  onError: () => {
    loading.value = false;
  },
});

const filteredResponses = computed(() => {
  let filtered = responses.value;

  if (categoryFilter.value) {
    filtered = filtered.filter((r) => r.category === categoryFilter.value);
  }

  if (searchTerm.value) {
    const search = searchTerm.value.toLowerCase();
    filtered = filtered.filter(
      (r) =>
        r.title.toLowerCase().includes(search) ||
        (r.shortcut && r.shortcut.toLowerCase().includes(search)) ||
        stripHtml(r.message).toLowerCase().includes(search)
    );
  }

  return filtered;
});

function setCategoryFilter(category) {
  categoryFilter.value = categoryFilter.value === category ? null : category;
}

function filterResponses() {
  // Filtering is done via computed property
}

function selectResponse(response) {
  props.onSelect(response);

  // Mark as used
  createResource({
    url: 'helpdesk.helpdesk.doctype.hd_canned_response.hd_canned_response.use_canned_response',
    makeParams: () => ({
      name: response.name,
    }),
  }).submit();
}

function stripHtml(html) {
  const tmp = document.createElement('DIV');
  tmp.innerHTML = html;
  return tmp.textContent || tmp.innerText || '';
}

function loadResponses() {
  loading.value = true;
  cannedResponsesResource.fetch();
}

onMounted(() => {
  loadResponses();
});

defineExpose({
  loadResponses,
});
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
