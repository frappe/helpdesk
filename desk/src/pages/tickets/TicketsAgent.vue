<template>
  <div class="flex flex-col">
    <PageTitle title="Tickets">
      <template #right>
        <RouterLink :to="{ name: 'TicketAgentNew' }">
          <Button label="New ticket" theme="gray" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </PageTitle>
    <div class="mx-5 mt-2.5 flex items-center justify-between">
      <!-- <PresetFilters doctype="HD Ticket" /> -->
      <div class="flex items-center gap-2">
        <FilterPopover doctype="HD Ticket" :resource="tickets" />
        <Dropdown :options="sortOptions">
          <template #default>
            <Button :label="getOrder() || 'Sort'" variant="outline" size="sm">
              <template #prefix>
                <LucideArrowDownUp class="h-4 w-4" />
              </template>
            </Button>
          </template>
        </Dropdown>
        <ColumnSelector doctype="HD Ticket" />
      </div>
    </div>
    <TicketsAgentList :resource="tickets" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { createResource, usePageMeta, Button, Dropdown } from 'frappe-ui';
import { AGENT_PORTAL_TICKET } from '@/router';
import { useAuthStore } from '@/stores/auth';
import { useFilter } from '@/composables/filter';
import { useOrder } from '@/composables/order';
import { createListManager } from '@/composables/listManager';
import { ColumnSelector, FilterPopover, PageTitle } from '@/components';
import TicketsAgentList from './TicketsAgentList.vue';
import PresetFilters from './PresetFilters.vue';

const { userId } = useAuthStore();
const { getArgs } = useFilter('HD Ticket');
const { get: getOrder, set: setOrder } = useOrder();
const pageLength = ref(20);
const tickets = createListManager({
  doctype: 'HD Ticket',
  pageLength: pageLength.value,
  orderBy: getOrder(),
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.class = {
        'font-medium': !d._seen?.includes(userId),
      };
      d.onClick = {
        name: AGENT_PORTAL_TICKET,
        params: {
          ticketId: d.name,
        },
      };
      d.conversation = {
        incoming: d.count_msg_incoming,
        outgoing: d.count_msg_outgoing,
        comments: d.count_comment,
      };
      d.source = d.via_customer_portal ? 'Customer portal' : 'Email';
    }
    return data;
  },
});

const sortOptionsRes = createResource({
  url: 'helpdesk.extends.doc.sort_options',
  auto: true,
  params: {
    doctype: 'HD Ticket',
  },
});
const sortOptions = computed(() => {
  return sortOptionsRes.data?.map((o) => ({
    label: o,
    onClick: () => setOrder(o),
  }));
});

usePageMeta(() => {
  return {
    title: 'Tickets',
  };
});
</script>
