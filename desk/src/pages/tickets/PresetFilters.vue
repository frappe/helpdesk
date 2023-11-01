<template>
  <Dropdown :options="options">
    <template #default="{ open }">
      <Button :label="title" theme="gray" variant="subtle">
        <template #suffix>
          <LucideChevronUp v-if="open" class="h-4 w-4 text-gray-700" />
          <LucideChevronDown v-else class="h-4 w-4 text-gray-700" />
        </template>
      </Button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { createListResource, Dropdown } from 'frappe-ui';
import { useAuthStore } from '@/stores/auth';
import { useFilter } from '@/composables/filter';

const authStore = useAuthStore();
const title = 'foobar';
const _r = createListResource({
  doctype: 'HD Preset Filter',
  auto: true,
  fields: [
    'name',
    'title',
    'type',
    {
      filters: ['label', 'fieldname', 'filter_type', 'value'],
    },
  ],
  transform: (data) => {
    for (const d of data) {
      for (const f of d.filters) {
        if (f.value === '@me') {
          f.value = authStore.userId;
        }
      }
    }
    return data;
  },
});
const options = computed(() => {
  const { apply, storage } = useFilter('HD Ticket');
  return (_r.data || []).reduce((p, c) => {
    const _g = p.find((i) => i.group === c.type);
    if (!_g) p.push({ group: c.type, items: [] });
    p.find((i) => i.group === c.type).items.push({
      label: c.title,
      onClick: () => {
        storage.value.clear();
        for (const f of c.filters) {
          storage.value.add({
            fieldname: f.fieldname,
            operator: f.filter_type,
            value: f.value,
            label: f.label,
          });
        }
        apply();
      },
    });
    return p;
  }, []);
});
</script>
