<template>
  <div class="divide-y overflow-auto px-5 pb-32">
    <div v-for="c in conversation" :id="c.name" :key="c.name" class="mt-4">
      <TicketComment
        v-if="c.commented_by"
        :name="c.name"
        :content="c.content"
        :date="c.creation"
        :user="c.user"
        :is-pinned="c.is_pinned"
      />
      <TicketCommunication
        v-else
        :content="c.content"
        :date="c.creation"
        :user="c.user"
        :sender-image="c.sender"
        :cc="c.cc || ''"
        :bcc="c.bcc || ''"
        :attachments="c.attachments"
      >
        <template #top-right="d">
          <Button label="To & Cc" @click="showPopup(c)" />
          <slot name="communication-top-right" v-bind="d" />
        </template>
      </TicketCommunication>
      <Dialog v-model="showPopupDialog" :options="{ size: 'xl', position: 'top' }">
        <template #body>
          <div class="relative">
            <div class="px-4.5 mb-2.5 text-base text-gray-600">
              <div style="overflow-wrap: break-word;">
                <!-- <b>To:</b> {{ recipientsToString(currentConversation.recipients) }}<br>
                <b>CC:</b> {{ currentConversation.cc }} -->
                <table>
                  <tr>
                  <td style="vertical-align: top;"><b>To:</b></td>
                  <td>{{ recipientsToString(currentConversation.recipients) }}</td>
                  </tr>
                  <tr>
                  <td style="vertical-align: top;"><b>CC:</b></td>
                  <td>{{ currentConversation.cc }}</td>
                  </tr>
                </table>
              </div>
            </div>
          </div>
        </template>
      </Dialog>
      <!-- <div>{{c.recipients}}</div> -->
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, nextTick, watch, ref } from "vue";
import { useRoute } from "vue-router";
import { useElementVisibility } from "@vueuse/core";
import { orderBy } from "lodash";
import { Dropdown, FeatherIcon, Dialog, Button } from "frappe-ui";
import { dayjs } from "@/dayjs";
import TicketComment from "./TicketComment.vue";
import TicketCommunication from "./TicketCommunication.vue";
import { ITicket } from "./symbols";

interface P {
  focus?: string;
}
const showPopupDialog = ref(false);
const currentConversation = ref(null);

const showPopup = (conversation) => {
  currentConversation.value = conversation;
  showPopupDialog.value = true;
};

function recipientsToString(value_){
  if (!Array.isArray(value_)) return "";
      return value_.join(", ");
};

const props = withDefaults(defineProps<P>(), {
  focus: "",
});
const route = useRoute();
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
  const hash = route.hash.slice(1);
  const id = hash || conversation.value.slice(-1).pop()?.name;
  if (id) setTimeout(() => scroll(id), 1000);
});


</script>
