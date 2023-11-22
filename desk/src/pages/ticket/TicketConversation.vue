<template>
  <div>
    <div class="sticky top-0 z-50 px-5 py-3 backdrop-blur-lg">
      <Button
        variant="subtle"
        label="Pinned"
        :theme="pinned ? 'blue' : 'gray'"
        @click="() => (pinned = !pinned)"
      >
        <template #suffix>
          <Badge
            :label="comments.data?.filter((c) => c.is_pinned).length"
            theme="gray"
            variant="outline"
          />
        </template>
      </Button>
    </div>
    <div class="divide-y overflow-auto pb-32">
      <div
        v-for="c in comments.data?.filter((c) => (pinned ? c.is_pinned : true))"
        :id="c.name"
        :key="c.name"
      >
        <TicketCommentPrivate
          v-if="c.comment_type == 'Private'"
          :name="c.name"
          :content="c.content"
          :date="c.creation"
          :user="c.user"
          :is-pinned="c.is_pinned"
          :attachments="c.attachments"
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
  </div>
</template>

<script setup lang="ts">
import { inject, ref } from 'vue';
import { Badge } from 'frappe-ui';
import TicketCommentPrivate from './TicketCommentPrivate.vue';
import TicketCommentPublic from './TicketCommentPublic.vue';
import { Ticket, Comments } from './symbols';

interface P {
  focus?: string;
}

const props = withDefaults(defineProps<P>(), {
  focus: '',
});
const ticket = inject(Ticket);
const comments = inject(Comments);
const pinned = ref(false);

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
