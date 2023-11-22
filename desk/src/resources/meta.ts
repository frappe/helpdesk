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
      // Remove hide fields
      .filter((f) => !f.hide)
      // Sort fields by `label`
      .sort((a, b) => a.label?.localeCompare(b.label))
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
      index: 2,
    },
    status: {
      width: 'w-20',
      index: 3,
    },
    priority: {
      width: 'w-20',
      index: 4,
    },
    ticket_type: {
      label: 'Type',
      index: 5,
    },
    assignee: {
      label: 'Assignee',
      width: 'w-40',
      index: 6,
      hide: !authStore.isAgent,
    },
    conversation: {
      label: 'Conversation',
      width: 'w-32',
      index: 7,
      hide: !authStore.isAgent,
    },
    source: {
      label: 'Source',
      hide: !authStore.isAgent,
    },
    creation: {
      label: 'Created',
      type: 'timeAgo',
      index: 100,
    },
    modified: {
      label: 'Updated',
      type: 'timeAgo',
      index: 101,
    },
    agent_group: {
      hide: !authStore.isAgent,
    },
    response_by: {
      hide: !authStore.isAgent,
    },
    resolution_by: {
      hide: !authStore.isAgent,
    },
    agreement_status: {
      hide: !authStore.isAgent,
    },
  },
  Contact: {
    name: {
      label: 'Name',
      width: 'w-80',
    },
    email_id: {
      label: 'Email',
      width: 'w-80',
    },
    phone: {
      label: 'Phone',
      key: 'phone',
      width: 'w-80',
    },
  },
  'HD Customer': {
    name: {
      label: 'Name',
      width: 'w-80',
    },
    domain: {
      label: 'Domain',
      width: 'w-80',
    },
  },
  'HD Team': {
    name: {
      label: 'Name',
      width: 'w-80',
    },
    assignment_rule: {
      label: 'Assignment rule',
      width: 'w-80',
    },
  },
  'HD Agent': {
    name: {
      label: 'name',
      width: 'w-80',
    },
    email: {
      label: 'email',
      width: 'w-80',
    },
    username: {
      label: 'username',
      width: 'w-80',
    },
    is_active: {
      hide: true,
    },
  },
  'HD Escalation Rule': {
    priority: {
      label: 'Priority',
      width: 'w-64',
    },
    team: {
      label: 'Team',
      width: 'w-64',
    },
    ticket_type: {
      label: 'Ticket type',
      width: 'w-64',
    },
    is_enabled: {
      label: 'Status',
      width: 'w-20',
    },
  },
  'HD Canned Response': {
    name: {
      label: 'Name',
      width: 'w-80',
    },
    owner: {
      label: 'Owner',
      key: 'owner',
      width: 'w-96',
    },
  },
}));
