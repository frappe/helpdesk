<template>
  <!-- column-reverse: opens on the newest message and stays pinned there. -->
  <div class="flex flex-col-reverse overflow-y-auto [overflow-anchor:none]">
    <div class="flex min-h-full shrink-0 flex-col">
      <div v-if="paginate?.hasNextPage" class="flex justify-center pb-3">
        <Button
          :label="__('Load older messages')"
          :loading="paginate.isFetchingNextPage"
          @click="paginate.fetchNextPage()"
        />
      </div>
      <ul
        role="log"
        aria-relevant="additions"
        :aria-label="__('Conversation')"
        class="flex flex-col gap-3 pb-4"
      >
        <template v-for="row in rows" :key="row.key">
          <li
            v-if="row.kind === 'day'"
            role="presentation"
            class="flex items-center gap-3 py-1"
          >
            <span class="flex-1 border-t border-outline-gray-2" />
            <span class="text-xs text-ink-gray-6">{{ row.label }}</span>
            <span class="flex-1 border-t border-outline-gray-2" />
          </li>

          <!-- A ticket event, not a message: centred, on neither side. -->
          <li v-else-if="row.kind === 'event'" class="flex justify-center">
            <span
              class="inline-flex max-w-full items-center gap-1.5 rounded-full bg-surface-gray-2 px-2.5 py-1 text-xs text-ink-gray-6"
            >
              <component
                :is="row.activity.icon"
                v-if="row.activity.icon"
                class="size-3.5 shrink-0"
                aria-hidden="true"
              />
              <span class="truncate">{{ row.activity.data.text }}</span>
              <span aria-hidden="true">·</span>
              <Tooltip :text="dateFormat(row.activity.timestamp)">
                <time
                  class="shrink-0"
                  :datetime="dayjsLocal(row.activity.timestamp).format()"
                >
                  {{
                    dayjsLocal(row.activity.timestamp).format(
                      DATE_FORMATS.clock
                    )
                  }}
                </time>
              </Tooltip>
            </span>
          </li>

          <li
            v-else
            class="flex gap-2"
            :class="{ 'flex-row-reverse': row.isCustomer }"
          >
            <Avatar
              v-if="!row.isCustomer"
              class="shrink-0 self-start"
              size="lg"
              :label="row.activity.author?.fullname"
              :image="row.activity.author?.image"
            />
            <PortalChatBubble
              :activity="row.activity"
              :is-customer="row.isCustomer"
              :is-viewer="row.isViewer"
            />
          </li>
        </template>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar, Button, Tooltip } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { DATE_FORMATS } from "@helpdesk/shared/utils";
import { dateFormat, dayjsLocal } from "@helpdesk/shared/timezone";
import type { Pagination } from "@framework/ui/components/ActivityTimeline";
import type { ChatRow } from "@app/composables/useChatRows";
import PortalChatBubble from "./PortalChatBubble.vue";

defineProps<{ rows: ChatRow[]; paginate?: Pagination }>();
</script>
