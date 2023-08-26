<template>
  <div class="divide-y overflow-scroll px-5 pb-32">
    <div v-for="c in conversation" :id="c.name" :key="c.name" class="mt-4">
      <TicketComment
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
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, nextTick, watch } from "vue";
import { useElementVisibility } from "@vueuse/core";
import { orderBy } from "lodash";
import { dayjs } from "@/dayjs";
// import { emitter } from "@/emitter";
import CommunicationItem from "@/components/CommunicationItem.vue";
import TicketComment from "./TicketComment.vue";
import { ITicket } from "./symbols";

interface P {
  focus?: string;
}

const props = withDefaults(defineProps<P>(), {
  focus: "",
});
const ticket = inject(ITicket);
const data = computed(() => ticket.data || {});
const communications = computed(() => data.value.communications || []);
const comments = computed(() => data.value.comments || []);
const conversation = computed(() =>
  orderBy([...communications.value, ...comments.value], (c) =>
    dayjs(c.creation)
  )
);

function scroll(id: string) {
  const e = document.getElementById(id);
  if (!useElementVisibility(e).value) {
    e.scrollIntoView({ behavior: "smooth" });
    e.focus();
  }
}

watch(
  () => props.focus,
  (id: string) => scroll(id)
);
nextTick(() => {
  const id = conversation.value.slice(-1).pop()?.name;
  if (id) setTimeout(() => scroll(id), 1000);
});
</script>
