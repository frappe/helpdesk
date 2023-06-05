<template>
  <router-link
    :to="toRoute"
    class="group flex justify-between"
    :class="{
      'text-gray-700': isSeen,
      'text-gray-900': !isSeen,
      'font-medium': !isSeen,
    }"
  >
    <div class="line-clamp-1">
      {{ subject }}
    </div>
    <div class="mx-2 flex items-center gap-2">
      <div
        class="flex gap-2 opacity-0 transition"
        :class="{
          'group-hover:opacity-100': conversationCount || commentCount,
        }"
      >
        <div v-if="conversationCount" class="flex items-center gap-1 text-xs">
          <IconMail class="h-3 w-3" />
          {{ conversationCount }}
        </div>
        <div v-if="commentCount" class="flex items-center gap-1 text-xs">
          <IconComment class="h-3 w-3" />
          {{ commentCount }}
        </div>
      </div>
      <div class="flex items-center gap-1 text-xs">
        <IconHash class="h-3 w-3" />
        {{ ticketName }}
      </div>
    </div>
  </router-link>
</template>

<script setup lang="ts">
import { computed, toRefs } from "vue";
import { createDocumentResource } from "frappe-ui";
import IconHash from "~icons/espresso/hash";
import IconMail from "~icons/espresso/mail";
import IconComment from "~icons/espresso/comment";

const props = defineProps({
  ticketName: {
    type: String,
    required: true,
  },
});

const { ticketName } = toRefs(props);
const toRoute = computed(() => ({
  name: "DeskTicket",
  params: {
    ticketId: ticketName.value,
  },
}));
const subject = computed(() => ticket.doc?.subject);
const metaData = computed(() => ticket.getMeta?.data?.message);
const conversationCount = computed(() => metaData.value?.conversation_count);
const commentCount = computed(() => metaData.value?.comment_count);
const isSeen = computed(() => metaData.value?.is_seen);

const ticket = createDocumentResource({
  doctype: "HD Ticket",
  name: ticketName,
  cache: ["Ticket", ticketName],
  whitelistedMethods: {
    getMeta: {
      method: "get_meta",
      cache: ["TicketMetaData", ticketName],
    },
  },
});

ticket.getMeta.fetch();
</script>

<style scoped>
.badge-new {
  padding: 3px 6px;
  width: 38px;
  height: 20px;
  border-radius: 5px;
}
</style>
