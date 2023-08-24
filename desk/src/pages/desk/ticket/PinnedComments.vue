<template>
  <div v-if="pinnedComments.length" class="border-b">
    <div
      class="flex cursor-pointer select-none items-center justify-between px-5 py-2 hover:bg-gray-50"
      @click="isExpanded = !isExpanded"
    >
      <div class="flex gap-1">
        <div class="text-base font-medium text-gray-900">Pinned comments</div>
        <div class="text-base text-gray-600">
          {{ "(" + pinnedComments.length + ")" }}
        </div>
      </div>
      <Icon :icon="isExpanded ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
    </div>
    <div v-if="isExpanded" class="divide-y px-5">
      <div
        v-for="c in pinnedComments"
        :key="c.name"
        class="flex cursor-pointer gap-2 p-2 text-base text-gray-900 hover:bg-gray-50"
        @click="emitter.emit('ticket:focus', c.name)"
      >
        <Avatar
          :label="userStore.getUser(c.commented_by).full_name"
          :image="userStore.getUser(c.commented_by).user_image"
          size="sm"
        />
        <div
          class="prose prose-sm line-clamp-1"
          v-html="sanitizeHtml(c.content)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Avatar } from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { Icon } from "@iconify/vue";
import { emitter } from "@/emitter";
import { useUserStore } from "@/stores/user";
import { useTicket } from "./data";

const isExpanded = ref(false);
const userStore = useUserStore();
const ticket = useTicket();
const comments = computed(() => ticket.value.data.comments || []);
const pinnedComments = computed(() =>
  comments.value.filter((c) => c.is_pinned)
);
</script>
