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
          'group-hover:opacity-100': communications || comments,
        }"
      >
        <div v-if="communications" class="flex items-center gap-1 text-xs">
          <IconMail class="h-3 w-3" />
          {{ communications }}
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
import { computed, toRefs } from "vue";
import { useAuthStore } from "@/stores/auth";
import IconComment from "~icons/lucide/message-square";
import IconHash from "~icons/espresso/hash";
import IconMail from "~icons/lucide/mail";

const props = defineProps({
  name: {
    type: Number,
    required: true,
  },
  subject: {
    type: String,
    required: true,
  },
  communications: {
    type: Number,
    required: false,
    default: 0,
  },
  comments: {
    type: Number,
    required: false,
    default: 0,
  },
  seen: {
    type: String,
    required: false,
    default: "",
  },
});

const authStore = useAuthStore();
const { name, seen } = toRefs(props);
const isSeen = computed(() => seen.value?.includes(authStore.userId));
const toRoute = computed(() => ({
  name: "DeskTicket",
  params: {
    ticketId: name.value,
  },
}));
</script>
