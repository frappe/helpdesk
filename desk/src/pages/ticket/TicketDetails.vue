<template>
  <div class="flex min-w-[300px] max-w-[300px] flex-col">
    <div class="border-b border-l px-5 py-1.5">
      <span class="text-base font-medium"> Details </span>
    </div>
    <div class="overflow-auto">
      <div class="border-l">
        <span>
          <div
            class="mx-5 flex flex-col justify-between gap-3.5 py-6 text-base"
          >
            <div class="space-y-1.5">
              <span class="block text-sm text-gray-700">ID</span>
              <span class="block break-words font-medium text-gray-900">
                {{ id }}
              </span>
            </div>
            <div v-if="data.customer" class="space-y-1.5">
              <span class="block text-sm text-gray-700">Customer</span>
              <span class="block break-words font-medium text-gray-900">
                {{ data.customer }}
              </span>
            </div>
            <div
              v-if="data.first_responded_on || data.response_by"
              class="space-y-1.5"
            >
              <div class="text-sm text-gray-700">First response</div>
              <div class="mr-2 inline-block font-medium text-gray-900">
                {{ dayjs(data.first_responded_on || data.response_by).short() }}
              </div>
              <span v-if="data.response_by">
                <Badge
                  v-if="!data.first_responded_on"
                  label="Due"
                  theme="orange"
                  variant="outline"
                />
                <Badge
                  v-else-if="
                    dayjs(data.first_responded_on).isBefore(
                      dayjs(data.response_by)
                    )
                  "
                  label="Fulfilled"
                  theme="green"
                  variant="outline"
                />
                <Badge v-else label="Failed" theme="red" variant="outline" />
              </span>
            </div>
            <div
              v-if="data.resolution_date || data.resolution_by"
              class="space-y-1.5"
            >
              <span class="block text-sm text-gray-700">Resolution</span>
              <span class="mr-2 font-medium text-gray-900">
                {{ dayjs(data.resolution_date || data.resolution_by).short() }}
              </span>
              <Badge
                v-if="
                  dayjs(data.resolution_date || undefined).isAfter(
                    data.resolution_by
                  )
                "
                label="Failed"
                theme="red"
                variant="outline"
              />
              <Badge
                v-else-if="!data.resolution_date"
                label="Due"
                theme="orange"
                variant="outline"
              />
              <Badge
                v-else-if="
                  dayjs(data.resolution_date).isBefore(data.resolution_by)
                "
                label="Fulfilled"
                theme="green"
                variant="outline"
              />
            </div>
            <div class="space-y-1.5">
              <span class="block text-sm text-gray-700">Modified</span>
              <Tooltip :text="dayjs(data.modified).long()">
                <span class="block break-words font-medium text-gray-900">
                  {{ dayjs(data.modified).fromNow() }}
                </span>
              </Tooltip>
            </div>
            <div class="space-y-1.5">
              <span class="block text-sm text-gray-700">Source</span>
              <span class="block break-words font-medium text-gray-900">
                {{ data.via_customer_portal ? 'Portal' : 'Mail' }}
              </span>
            </div>
            <div v-if="data.feedback_rating" class="space-y-1.5">
              <span class="block text-sm text-gray-700">Feedback</span>
              <StarRating :rating="data.feedback_rating" />
              <span class="block font-medium text-gray-900">
                {{ data.feedback_text }}
              </span>
              <span class="block text-gray-900">
                {{ data.feedback_extra }}
              </span>
            </div>
          </div>
        </span>
      </div>
      <img :src="TicketDivider" />
      <div class="grow truncate border-l p-5">
        <div v-if="authStore.isAgent" class="flex flex-col gap-3">
          <div v-for="o in options" :key="o.field" class="space-y-1.5">
            <span class="block text-sm text-gray-700">
              {{ o.label }}
            </span>
            <Autocomplete
              :options="o.store.dropdown"
              :placeholder="`Select a ${o.label}`"
              :value="data[o.field]"
              @change="(e) => ticket.setValue.submit({ [o.field]: e.value })"
            />
          </div>
          <UniInput
            v-for="f in template.doc?.fields"
            :key="f.fieldname"
            :field="f"
            :value="data[f.fieldname]"
            @change="(e) => ticket.setValue.submit({ [f.fieldname]: e.value })"
          />
        </div>
        <div v-else class="flex flex-col gap-3">
          <div
            v-for="f in template.doc?.fields.filter(
              (f) => !f.hide_from_customer
            )"
            :key="f.fieldname"
            class="space-y-1.5"
          >
            <div class="text-sm text-gray-700">
              {{ f.label }}
            </div>
            <div class="break-words text-base font-medium text-gray-900">
              {{ ticket.doc[f.fieldname] || '—' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue';
import { createDocumentResource, Autocomplete, Tooltip } from 'frappe-ui';
import { dayjs } from '@/dayjs';
import { useAuthStore } from '@/stores/auth';
import { useTeamStore } from '@/stores/team';
import { useTicketPriorityStore } from '@/stores/ticketPriority';
import { useTicketTypeStore } from '@/stores/ticketType';
import { StarRating, UniInput } from '@/components';
import { Id, Ticket } from './symbols';
import TicketSidebarHeader from './TicketSidebarHeader.vue';
import TicketDivider from '@/assets/misc/ticket-divider.svg';

const authStore = useAuthStore();
const id = inject(Id);
const ticket = inject(Ticket);
const data = computed(() => ticket.doc);
const template = createDocumentResource({
  doctype: 'HD Ticket Template',
  name: ticket.doc?.template,
  auto: !!ticket.doc?.template,
});
const options = computed(() => [
  {
    field: 'ticket_type',
    label: 'Ticket type',
    store: useTicketTypeStore(),
  },
  {
    field: 'priority',
    label: 'Priority',
    store: useTicketPriorityStore(),
  },
  {
    field: 'agent_group',
    label: 'Team',
    store: useTeamStore(),
  },
]);
</script>
