<template>
  <div v-if="typingUsers.length > 0" class="pl-2">
    <div class="flex items-center gap-2 text-sm text-gray-600">
      <div class="flex items-center gap-1.5">
        <component :is="typingMessage" />
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTyping } from "@/composables/realtime";
import { useUserStore } from "@/stores/user";
import { computed, h, onBeforeUnmount } from "vue";
import UserAvatar from "./UserAvatar.vue";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const { typingUsers, cleanup } = useTyping(props.ticketId);

const typingMessage = computed(() => {
  const count = typingUsers.length;
  if (count === 0) return null;
  const { getUser } = useUserStore();
  let firstUser = getUser(typingUsers[0])?.full_name || typingUsers[0];
  console.log(firstUser);
  console.log(typingUsers);

  if (count === 1) {
    return h("div", { class: "flex items-center gap-1" }, [
      h(UserAvatar, { name: typingUsers[0], size: "sm" }),
      h("span", { class: "text-ink-gray-6 font-medium" }, firstUser),
      h("span", { class: "text-ink-gray-5" }, " is typing"),
    ]);
  } else if (count === 2) {
    return h("div", { class: "flex items-center gap-1" }, [
      h("span", { class: "text-ink-gray-6 font-medium" }, firstUser),
      h("span", { class: "text-ink-gray-5" }, " and "),
      h(
        "span",
        { class: "text-ink-gray-6 font-medium" },
        getUser(typingUsers[1])?.full_name
      ),
      h("span", { class: "text-ink-gray-5" }, " are typing"),
    ]);
  } else {
    return h("div", { class: "flex items-center gap-1" }, [
      h("span", { class: "text-ink-gray-6 font-medium" }, firstUser),
      h("span", { class: "text-ink-gray-5" }, " and "),
      h(
        "span",
        { class: "text-ink-gray-6 font-medium" },
        `${count - 1} others`
      ),
      h("span", { class: "text-ink-gray-5" }, " are typing"),
    ]);
  }
});

onBeforeUnmount(() => {
  cleanup();
});
</script>

<style scoped>
.typing-dots {
  display: inline-flex;
  gap: 2px;
  align-items: center;
}

.typing-dots span {
  height: 4px;
  width: 4px;
  background-color: #6b7280;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
