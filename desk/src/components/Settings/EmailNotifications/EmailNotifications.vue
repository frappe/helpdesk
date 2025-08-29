<template>
  <div class="px-10 h-full overflow-y-auto flex flex-col isolate">
    <NotificationList v-if="curNotification === null" :onSelect="onSelect" />
    <component
      v-else
      :is="notificationToComponent[curNotification.name]"
      :onBack="resetCurNotification"
      :notification="curNotification"
    ></component>
  </div>
</template>

<script setup lang="ts">
import { type Component, markRaw, ref } from "vue";
import type { Notification, NotificationName } from "./types";
import NotificationList from "./NotificationList.vue";
import Acknowledgement from "./Acknowledgement.vue";
import ReplyViaAgent from "./ReplyViaAgent.vue";
import ShareFeedback from "./ShareFeedback.vue";
import ReplyToAgents from "./ReplyToAgents.vue";

const curNotification = ref<Notification | null>(null);

const notificationToComponent: Record<
  NotificationName,
  Component<{ onBack: () => void; notification: Notification }>
> = {
  share_feedback: markRaw(ShareFeedback),
  acknowledgement: markRaw(Acknowledgement),
  reply_to_agents: markRaw(ReplyToAgents),
  reply_via_agent: markRaw(ReplyViaAgent),
};

function resetCurNotification() {
  curNotification.value = null;
}

function onSelect(notification: Notification) {
  curNotification.value = notification;
}
</script>
