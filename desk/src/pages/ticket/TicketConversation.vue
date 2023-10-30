<template>
  <div class="divide-y overflow-auto px-5 pb-32">
    <div v-for="c in comments.data" :id="c.name" :key="c.name" class="mt-4">
      <TicketCommentPrivate
        v-if="c.comment_type == 'Private'"
        :name="c.name"
        :content="c.content"
        :date="c.creation"
        :user="c.user"
        :is-pinned="c.is_pinned"
      />
      <TicketCommentPublic
        v-else
        :content="c.content"
        :date="c.creation"
        :user="c.user"
        :cc="c.cc || ''"
        :bcc="c.bcc || ''"
        :attachments="c.attachments"
      >
        <template #top-right="d">
          <slot name="communication-top-right" v-bind="d" />
        </template>
      </TicketCommentPublic>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from "vue";
import TicketCommentPrivate from "./TicketCommentPrivate.vue";
import TicketCommentPublic from "./TicketCommentPublic.vue";
import { ITicket, Comments } from "./symbols";
import { createListManager } from "@/composables/listManager";

interface P {
  focus?: string;
}

const props = withDefaults(defineProps<P>(), {
  focus: "",
});
const ticket = inject(ITicket);
const comments = inject(Comments);

// function scroll(id: string) {
//   const e = document.getElementById(id);
//   if (!useElementVisibility(e).value) {
//     e.scrollIntoView({ behavior: "smooth" });
//     e.focus();
//   }
// }
//
// watch(
//   () => props.focus,
//   (id: string) => scroll(id)
// );
// nextTick(() => {
//   const hash = route.hash.slice(1);
//   const id = hash || conversation.value.slice(-1).pop()?.name;
//   if (id) setTimeout(() => scroll(id), 1000);
// });
</script>
