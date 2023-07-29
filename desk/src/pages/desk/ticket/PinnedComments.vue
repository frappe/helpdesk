<template>
  <div v-if="comments.length" class="border-b">
    <div
      class="flex cursor-pointer select-none items-center justify-between px-7 py-3"
      @click="isExpanded = !isExpanded"
    >
      <div class="flex gap-1">
        <div class="text-base font-medium text-gray-900">Pinned comments</div>
        <div class="text-base text-gray-600">
          {{ "(" + comments.length + ")" }}
        </div>
      </div>
      <Icon :icon="isExpanded ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
    </div>
    <div v-if="isExpanded" class="divide-y px-5">
      <div
        v-for="c in comments"
        :key="c.name"
        class="flex cursor-pointer gap-2 p-2 text-base text-gray-900 hover:bg-gray-50"
        @click="emitter.emit('ticket:focus', c.name)"
      >
        <Avatar
          :label="userStore.getUser(c.commented_by).full_name"
          :image="userStore.getUser(c.commented_by).user_image"
          size="sm"
        />
        <div class="prose prose-sm line-clamp-1" v-html="c.content" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Avatar } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { Comment } from "@/types";
import { emitter } from "@/emitter";
import { useUserStore } from "@/stores/user";
import { useTicketStore } from "./data";

const userStore = useUserStore();
const ticketStore = useTicketStore();
const isExpanded = ref(false);
const comments = computed(() =>
  (ticketStore.doc.comments || []).filter((c: Comment) => c.is_pinned)
);
</script>
