<template>
  <div class="flex flex-col overflow-hidden">
    <div class="flex w-full flex-col items-center gap-4 overflow-auto">
      <div class="content mb-32 divide-y">
        <div v-for="c in conversation" :id="c.name" :key="c.name" class="mt-4">
          <CommentItem
            v-if="c.commented_by"
            :name="c.name"
            :content="c.content"
            :date="c.creation"
            :sender="c.commented_by"
            :is-pinned="c.is_pinned"
          />
          <CommunicationItem
            v-else
            :content="c.content"
            :date="c.creation"
            :sender="c.sender"
            :sender-image="c.sender"
            :cc="c.cc || ''"
            :bcc="c.bcc || ''"
            :attachments="c.attachments"
          >
            <template #top-right="{ content, cc, bcc }">
              <Dropdown :options="dropdownOptions(content, cc, bcc)">
                <Button theme="gray" variant="ghost">
                  <template #icon>
                    <Icon icon="lucide:more-horizontal" />
                  </template>
                </Button>
              </Dropdown>
            </template>
          </CommunicationItem>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button, Dropdown } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { orderBy } from "lodash";
import { Icon } from "@iconify/vue";
import { emitter } from "@/emitter";
import CommunicationItem from "@/components/CommunicationItem.vue";
import CommentItem from "./CommentItem.vue";
import IconReply from "~icons/lucide/reply";
import IconReplyAll from "~icons/lucide/reply-all";
import { useTicketStore, useTicket } from "./data";

const ticketStore = useTicketStore();
const ticket = useTicket();
const data = computed(() => ticket.value.data);
const { editor } = ticketStore;
const communications = computed(() => data.value.communications || []);
const comments = computed(() => data.value.comments || []);
const conversation = computed(() =>
  orderBy([...communications.value, ...comments.value], (c) =>
    dayjs(c.creation)
  )
);
const last = computed(() => conversation.value.slice(-1).pop());

function dropdownOptions(content: string, cc: string, bcc: string) {
  return [
    {
      label: "Reply",
      icon: IconReply,
      onClick: () => {
        editor.cc = [];
        editor.bcc = [];
        editor.content = quote(content);
        editor.isExpanded = true;
      },
    },
    {
      label: "Reply All",
      icon: IconReplyAll,
      onClick: () => {
        editor.cc = cc.split(",");
        editor.bcc = bcc.split(",");
        editor.content = quote(content);
        editor.isExpanded = true;
      },
    },
  ];
}

function quote(s: string) {
  return `<blockquote>${s}</blockquote><br/>`;
}

if (last.value) {
  setTimeout(() => emitter.emit("ticket:focus", last.value.name), 1000);
}
</script>

<style scoped>
.content {
  width: 742px;
}
</style>
