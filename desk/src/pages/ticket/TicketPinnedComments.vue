<template>
  <div v-if="pinnedComments.length" class="border-b text-base">
    <div
      class="flex cursor-pointer select-none items-center justify-between px-5 py-2 hover:bg-gray-50"
      @click="isExpanded = !isExpanded"
    >
      <div class="flex gap-1">
        <div class="font-medium text-gray-900">Pinned comments</div>
        <div class="text-gray-600">
          {{ "(" + pinnedComments.length + ")" }}
        </div>
      </div>
      <Icon :icon="isExpanded ? 'lucide:chevron-up' : 'lucide:chevron-down'" />
    </div>
    <div v-if="isExpanded" class="divide-y px-5">
      <div
        v-for="c in pinnedComments"
        :key="c.name"
        class="flex cursor-pointer items-center gap-2 p-2 text-gray-900 hover:bg-gray-50"
        @click="$emit('focus', c.name)"
      >
        <UserAvatar :user="c.commented_by" expand strong />
        <span class="text-gray-500">&mdash;</span>
        <div
          class="prose prose-sm line-clamp-1"
          v-html="sanitizeHtml(c.content)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref } from "vue";
import sanitizeHtml from "sanitize-html";
import { Icon } from "@iconify/vue";
import { UserAvatar } from "@/components";
import { ITicket } from "./symbols";

interface E {
  (event: "focus", focus: string): void;
}

defineEmits<E>();
const isExpanded = ref(false);
const ticket = inject(ITicket);
const comments = computed(() => ticket.data.comments || []);
const pinnedComments = computed(() =>
  comments.value.filter((c) => c.is_pinned)
);
</script>
