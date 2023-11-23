<template>
  <div v-if="ticket.doc" class="flex flex-col">
    <TicketBreadcrumbs parent="TicketsAgent" :title="ticket.doc?.subject">
      <template #right>
        <TicketAgentActions v-if="authStore.isAgent" />
        <TicketCustomerActions v-else />
      </template>
    </TicketBreadcrumbs>
    <div class="flex overflow-hidden">
      <Tabs
        v-model="tab"
        :tabs="[
          {
            label: 'Comments',
            component: TicketComments,
          },
          {
            label: 'History',
            component: TicketHistory,
          },
          {
            label: 'Views',
            component: TicketViews,
          },
        ]"
      >
        <template #default="{ tab }">
          <component :is="tab.component" class="grow" />
        </template>
      </Tabs>
      <TicketDetails />
    </div>
  </div>
</template>

<script setup lang="ts">
import { provide, ref } from 'vue';
import {
  createResource,
  createDocumentResource,
  createListResource,
  usePageMeta,
  Button,
  FormControl,
  Tabs,
  TabButtons,
} from 'frappe-ui';
import { emitter } from '@/emitter';
import { useAuthStore } from '@/stores/auth';
import { useError } from '@/composables';
import { trackVisit } from '@/utils';
import { Id, Comments, Ticket } from './symbols';
import TicketAgentActions from './TicketAgentActions.vue';
import TicketAgentSidebar from './TicketAgentSidebar.vue';
import TicketBreadcrumbs from './TicketBreadcrumbs.vue';
import TicketCannedResponses from './TicketCannedResponses.vue';
import TicketConversation from './TicketConversation.vue';
import TicketCustomerActions from './TicketCustomerActions.vue';
import TicketDetails from './TicketDetails.vue';
import TicketViews from './TicketViews.vue';
import TicketHistory from './TicketHistory.vue';
import TicketComments from './TicketComments.vue';
import TicketPinnedComments from './TicketPinnedComments.vue';
import TicketTextEditor from './TicketTextEditor.vue';

const tab = ref(0);

interface P {
  ticketId: string;
}

const props = defineProps<P>();
const authStore = useAuthStore();
const ticket = createDocumentResource({
  doctype: 'HD Ticket',
  cache: ['Ticket', props.ticketId],
  name: props.ticketId,
  whitelistedMethods: {
    assign: 'assign_agent',
  },
  auto: true,
  onError: useError(),
  onSuccess: () => {
    comments.fetch();
    // trackVisit('HD Ticket', props.ticketId);
  },
});
const comments = createListResource({
  doctype: 'HD Comment',
  cache: ['Comments', props.ticketId],
  fields: [
    'name',
    'comment_type',
    'content',
    'creation',
    'is_pinned',
    'user',
    {
      attachments: ['file.file_url', 'file.file_name'],
    },
  ],
  filters: {
    reference_doctype: 'HD Ticket',
    reference_name: props.ticketId,
  },
  orderBy: 'creation asc',
  onError: useError(),
});
provide(Id, props.ticketId);
provide(Comments, comments);
provide(Ticket, ticket);
const showCannedResponses = ref(false);

usePageMeta(() => {
  return {
    title: ticket.doc?.subject,
  };
});
</script>
