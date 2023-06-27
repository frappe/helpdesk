<template>
  <RouterLink
    :to="toRoute"
    class="flex justify-between"
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
          'group-hover:opacity-100': conversations || comments,
        }"
      >
        <div v-if="conversations" class="flex items-center gap-1 text-xs">
          <IconMail class="h-3 w-3" />
          {{ conversations }}
        </div>
        <div v-if="comments" class="flex items-center gap-1 text-xs">
          <IconComment class="h-3 w-3" />
          {{ comments }}
        </div>
      </div>
      <div class="flex items-center gap-1 text-xs">
        <IconHash class="h-3 w-3" />
        {{ name }}
      </div>
    </div>
  </RouterLink>
</template>

<script setup lang="ts">
import { AGENT_PORTAL_TICKET } from "@/router";
import IconHash from "~icons/espresso/hash";
import IconMail from "~icons/lucide/mail";
import IconComment from "~icons/lucide/message-square";

const props = defineProps({
  name: {
    type: Number,
    required: true,
  },
  subject: {
    type: String,
    required: true,
  },
  comments: {
    type: Number,
    required: false,
    default: 0,
  },
  conversations: {
    type: Number,
    required: false,
    default: 0,
  },
  isSeen: {
    type: Boolean,
    required: false,
    default: true,
  },
});

const toRoute = {
  name: AGENT_PORTAL_TICKET,
  params: {
    ticketId: props.name,
  },
};
</script>
