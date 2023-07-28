<template>
  <div v-if="pinnedComments.length" class="border-b">
    <div
      class="flex cursor-pointer select-none items-center justify-between px-7 py-3"
      @click="isExpanded = !isExpanded"
    >
      <div class="flex gap-1">
        <div class="text-base font-medium text-gray-900">Pinned comments</div>
        <div class="text-base text-gray-600">
          {{ "(" + pinnedComments.length + ")" }}
        </div>
      </div>
      <Icon icon="lucide:chevron-down" />
    </div>
    <div v-if="isExpanded" class="divide-y px-5">
      <div
        v-for="comment in pinnedComments"
        :key="comment.name"
        class="flex cursor-pointer gap-2 p-2 text-base text-gray-900 hover:bg-gray-50"
        @click="focusedConversationItem = comment.name"
      >
        <Avatar
          :label="comment.sender.full_name"
          :image="comment.sender.user_image"
          size="sm"
        />
        <div class="prose prose-sm line-clamp-1" v-html="comment.content" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { storeToRefs } from "pinia";
import { Avatar } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { useTicketStore } from "./data";

const { ticket } = useTicketStore();
const { focusedConversationItem } = storeToRefs(useTicketStore());
const isExpanded = ref(false);
const pinnedComments = computed(() =>
  (ticket.getComments.data?.message || []).filter(
    (comment) => comment.is_pinned
  )
);
</script>
