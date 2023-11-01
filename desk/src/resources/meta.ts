import { computed, reactive } from 'vue';
import { createResource } from 'frappe-ui';
import { useAuthStore } from '@/stores/auth';
import { useError } from '@/composables';

const authStore = useAuthStore();
export const state = reactive({});
export const fetch = createResource({
  url: 'helpdesk.extends.client.get_meta',
  auto: false,
  transform: (data) => {
    if (!(data.name in override.value)) return data;
    // Keep track of additional fields
    let keys = [];
    keys.push(...Object.keys(override.value[data.name]));
    // Default values
    const _d = {
      width: 'w-32',
      align: 'left',
      text: 'text-gray-800',
      index: 99,
    };
    // Merge standard fields with override
    for (const f of data.fields) {
      Object.assign(f, _d);
      // Removed standard fields from `keys`
      if (keys.includes(f.fieldname)) {
        keys = keys.filter((k) => k !== f.fieldname);
      }
      // Actual merge
      if (f.fieldname in override.value[data.name]) {
        Object.assign(f, override.value[data.name][f.fieldname]);
      }
    }
    // Add additional fields
    for (const key of keys) {
      // Set default values
      Object.assign(override.value[data.name][key], {
        fieldname: key,
        in_list_view: 1,
        width: override.value[data.name][key].width || _d.width,
        text: override.value[data.name][key].text || _d.text,
        align: override.value[data.name][key].align || _d.align,
        index: override.value[data.name][key].index || _d.index,
      });
      data.fields.push(override.value[data.name][key]);
    }
    return data;
  },
  onError: useError(),
  onSuccess: (data) => {
    data.fields = data.fields
      // Remove hidden fields
      .filter((f) => !f.hidden)
      // Sort fields by `index`
      .sort((a, b) => a.index - b.index);
    state[data.name] = data;
  },
});
const override = computed(() => ({
  'HD Ticket': {
    name: {
      label: '#',
      width: 'w-8',
      text: 'text-xs',
      index: 1,
    },
    subject: {
      width: 'w-96',
      text: 'text-gray-900',
    },
    status: {
      width: 'w-20',
    },
    assignee: {
      label: 'Assignee',
      width: 'w-40',
      hidden: !authStore.isAgent,
    },
    conversation: {
      label: 'Conversation',
      width: 'w-32',
      hidden: !authStore.isAgent,
    },
    source: {
      label: 'Source',
      hidden: !authStore.isAgent,
    },
    creation: {
      label: 'Created',
    },
    modified: {
      label: 'Updated',
    },
  },
}));
