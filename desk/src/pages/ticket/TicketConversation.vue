<template>
  <div
    class="md:mx-5 md:my-8 mb-4 mt-8 flex items-center justify-between h-8 text-xl font-semibold text-gray-800"
  >
    Activity
  </div>
  <div class="overflow-auto px-5 pb-20 grow">
    <div
      v-for="c in communications"
      :id="c.name"
      :key="c.name"
      class="mt-4 flex items-between justify-center gap-4 relative"
    >
      <div
        class="w-full activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4"
      >
        <div
          class="relative flex justify-center after:absolute after:left-[50%] after:top-[12%] after:-z-10 after:border-l after:border-gray-200 after:h-full"
        >
          <Avatar
            size="lg"
            :label="c.user.name"
            :image="c.user.image"
            class="mt-1 relative"
          />
        </div>
        <TicketCommunication
          :content="c.content"
          :date="c.creation"
          :user="c.user"
          :sender-image="c.sender"
          :cc="c.cc || ''"
          :bcc="c.bcc || ''"
          :attachments="c.attachments"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, nextTick, watch } from "vue";
import { useRoute } from "vue-router";
import { useElementVisibility } from "@vueuse/core";
import { Avatar } from "frappe-ui";
import { orderBy } from "lodash";
import { dayjs } from "@/dayjs";
import TicketCommunication from "./TicketCommunication.vue";
import { ITicket } from "./symbols";

interface P {
  focus?: string;
}

const props = withDefaults(defineProps<P>(), {
  focus: "",
});
const route = useRoute();
const ticket = inject(ITicket);
const communications = computed(() => {
  const _communications = ticket.data.communications || [];
  return orderBy(_communications, (c) => dayjs(c.creation));
});

function isElementInViewport(el: HTMLElement) {
  if (!el) return false;
  const rect = el.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= window.innerHeight &&
    rect.right <= window.innerWidth
  );
}

function scroll(id: string) {
  const e = document.getElementById(id);
  if (!isElementInViewport(e)) {
    e.scrollIntoView();
  }
}

watch(
  () => props.focus,
  (id: string) => scroll(id)
);
nextTick(() => {
  const hash = route.hash.slice(1);
  const id = hash || communications.value.slice(-1).pop()?.name;
  if (id) setTimeout(() => scroll(id), 1000);
});
</script>
