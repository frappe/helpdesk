<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-2">
          <h1 class="text-2xl font-semibold">Canned Responses</h1>
        </div>
      </template>
      <template #right-header>
        <Button
          variant="solid"
          @click="createNew"
        >
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
          New Response
        </Button>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-y-auto p-6">
      <div class="mb-4 flex gap-4">
        <div class="flex-1">
          <input
            v-model="searchTerm"
            type="text"
            placeholder="Search canned responses..."
            class="form-input w-full"
          />
        </div>
        <div class="w-48">
          <FormControl
            type="select"
            v-model="categoryFilter"
            :options="['All', ...categories]"
            placeholder="Filter by category"
          />
        </div>
      </div>

      <div v-if="loading" class="text-center py-8">
        <LoadingIndicator />
      </div>

      <div v-else-if="filteredResponses.length === 0" class="text-center py-8">
        <div class="text-gray-500">
          <p class="text-lg mb-2">No canned responses found</p>
          <p class="text-sm">Create your first canned response to get started</p>
        </div>
      </div>

      <div v-else class="grid gap-4">
        <div
          v-for="response in filteredResponses"
          :key="response.name"
          class="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
          @click="editResponse(response.name)"
        >
          <div class="flex items-start justify-between mb-2">
            <div class="flex-1">
              <h3 class="font-semibold text-lg">{{ response.title }}</h3>
              <div class="flex items-center gap-2 mt-1">
                <Badge
                  v-if="response.shortcut"
                  :label="response.shortcut"
                  variant="subtle"
                />
                <Badge
                  v-if="response.category"
                  :label="response.category"
                  variant="subtle"
                />
                <Badge
                  v-if="!response.is_active"
                  label="Inactive"
                  variant="subtle"
                  theme="red"
                />
              </div>
            </div>
            <div class="text-right">
              <div class="text-sm text-gray-500">
                Used {{ response.usage_count || 0 }} times
              </div>
              <div v-if="response.last_used" class="text-xs text-gray-400 mt-1">
                Last used {{ timeAgo(response.last_used) }}
              </div>
            </div>
          </div>

          <div
            class="text-sm text-gray-600 mt-2 line-clamp-2"
            v-html="response.message"
          ></div>

          <div class="flex gap-2 mt-3">
            <Button
              size="sm"
              variant="ghost"
              @click.stop="editResponse(response.name)"
            >
              Edit
            </Button>
            <Button
              size="sm"
              variant="ghost"
              theme="red"
              @click.stop="deleteResponse(response.name)"
            >
              Delete
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Button, Badge, FormControl, createResource } from 'frappe-ui';
import { timeAgo } from '@/utils';
import { LayoutHeader } from '@/components';

const searchTerm = ref('');
const categoryFilter = ref('All');
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
  auto: false,
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

  if (categoryFilter.value && categoryFilter.value !== 'All') {
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

function stripHtml(html) {
  const tmp = document.createElement('DIV');
  tmp.innerHTML = html;
  return tmp.textContent || tmp.innerText || '';
}

function loadResponses() {
  loading.value = true;
  cannedResponsesResource.fetch();
}

function createNew() {
  window.open('/app/hd-canned-response/new', '_blank');
}

function editResponse(name) {
  window.open(`/app/hd-canned-response/${name}`, '_blank');
}

async function deleteResponse(name) {
  if (!confirm('Are you sure you want to delete this canned response?')) {
    return;
  }

  try {
    await createResource({
      url: 'frappe.client.delete',
      makeParams: () => ({
        doctype: 'HD Canned Response',
        name: name,
      }),
    }).submit();

    loadResponses();
  } catch (error) {
    console.error('Error deleting canned response:', error);
  }
}

onMounted(() => {
  loadResponses();
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
