<template>
  <div
    class="flex w-full"
    :class="isOutgoing ? 'justify-end' : 'justify-start'"
  >
    <div class="group relative max-w-[85%] sm:max-w-[75%]">
      <!-- Quoted reply -->
      <div
        v-if="activity.is_reply && activity.reply_message"
        class="mb-1 cursor-pointer rounded-md border-s-2 bg-surface-gray-2 px-2 py-1 text-p-xs text-ink-gray-6"
        :class="
          activity.reply_to_type === 'Incoming'
            ? 'border-outline-gray-3'
            : 'border-ink-green-3'
        "
        @click="emit('scrollTo', activity.reply_to)"
      >
        <div class="font-medium text-ink-gray-7">
          {{ activity.reply_to_from || __("You") }}
        </div>
        <div
          class="line-clamp-2"
          v-html="formatWhatsAppMessage(activity.reply_message)"
        />
      </div>

      <!-- Bubble -->
      <div
        :id="activity.key"
        class="rounded-lg px-3 py-2 text-p-sm shadow-sm"
        :class="
          isOutgoing
            ? 'bg-surface-green-2 text-ink-gray-8'
            : 'bg-surface-gray-2 text-ink-gray-8'
        "
      >
        <!-- Template -->
        <template v-if="activity.message_type === 'Template'">
          <div v-if="activity.header" class="mb-1 font-semibold">
            {{ activity.header }}
          </div>
          <div
            v-html="
              formatWhatsAppMessage(activity.template || activity.message)
            "
          />
          <div v-if="activity.footer" class="mt-1 text-p-xs text-ink-gray-5">
            {{ activity.footer }}
          </div>
        </template>

        <!-- Image -->
        <template v-else-if="activity.content_type === 'image'">
          <img
            v-if="activity.attach"
            :src="activity.attach"
            class="max-h-72 rounded-md"
            :alt="__('Image attachment')"
          />
          <span v-else class="text-p-xs italic text-ink-gray-5">
            {{ __("Attachment unavailable") }}
          </span>
          <div
            v-if="hasCaption"
            class="mt-1"
            v-html="formatWhatsAppMessage(activity.message)"
          />
        </template>

        <!-- Video -->
        <template v-else-if="activity.content_type === 'video'">
          <video
            v-if="activity.attach"
            :src="activity.attach"
            controls
            class="max-h-72 rounded-md"
          />
          <span v-else class="text-p-xs italic text-ink-gray-5">
            {{ __("Attachment unavailable") }}
          </span>
          <div
            v-if="hasCaption"
            class="mt-1"
            v-html="formatWhatsAppMessage(activity.message)"
          />
        </template>

        <!-- Audio -->
        <template v-else-if="activity.content_type === 'audio'">
          <audio
            v-if="activity.attach"
            :src="activity.attach"
            controls
            class="w-56 max-w-full"
          />
          <span v-else class="text-p-xs italic text-ink-gray-5">
            {{ __("Attachment unavailable") }}
          </span>
        </template>

        <!-- Document -->
        <AttachmentItem
          v-else-if="activity.content_type === 'document' && activity.attach"
          :label="documentName"
          :url="activity.attach"
        />

        <!-- Text / button / fallback -->
        <div v-else v-html="formatWhatsAppMessage(activity.message)" />

        <!-- Meta line -->
        <div
          class="mt-1 flex items-center justify-end gap-1 text-p-xs text-ink-gray-5"
        >
          <Badge
            v-if="fromOtherTicket"
            :label="`#${activity.hd_ticket}`"
            variant="subtle"
            theme="gray"
            size="sm"
          />
          <Tooltip :text="dateFormat(activity.creation, dateTooltipFormat)">
            <span>{{ timeAgo(activity.creation) }}</span>
          </Tooltip>
          <span v-if="isOutgoing" class="flex items-center">
            <Badge
              v-if="isFailed"
              :label="__('Failed')"
              variant="subtle"
              theme="red"
              size="sm"
            />
            <FeatherIcon
              v-else
              name="check"
              class="size-3"
              :class="isRead ? 'text-ink-blue-3' : 'text-ink-gray-4'"
            />
          </span>
        </div>
      </div>

      <!-- Reaction badge -->
      <div
        v-if="activity.reaction"
        class="absolute -bottom-3 rounded-full bg-surface-white px-1 text-sm shadow"
        :class="isOutgoing ? 'end-2' : 'start-2'"
      >
        {{ activity.reaction }}
      </div>

      <!-- Message actions: react + reply. Anchored inside the bubble's width
           (no negative offset that would overflow on mobile) and always visible
           on touch, hover-revealed on desktop. -->
      <div
        class="absolute -top-3 z-10 flex items-center gap-0.5 rounded-full bg-surface-white px-0.5 shadow-sm transition group-hover:opacity-100 sm:opacity-0"
        :class="isOutgoing ? 'end-1' : 'start-1'"
      >
        <IconPicker :reaction="true" @update:model-value="onReact">
          <template #default="{ togglePopover }">
            <Button variant="ghost" size="sm" @click="togglePopover()">
              <template #icon><ReactionIcon class="size-4" /></template>
            </Button>
          </template>
        </IconPicker>
        <Button variant="ghost" size="sm" @click="emit('reply', activity)">
          <template #icon><ReplyIcon class="size-4" /></template>
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AttachmentItem } from "@/components";
import IconPicker from "@/components/IconPicker.vue";
import ReactionIcon from "@/components/icons/ReactionIcon.vue";
import ReplyIcon from "@/components/icons/ReplyIcon.vue";
import { __ } from "@/translation";
import { TicketSymbol, WhatsAppActivity } from "@/types";
import { dateFormat, dateTooltipFormat, timeAgo } from "@/utils";
import { formatWhatsAppMessage } from "@/utils/whatsapp";
import { Badge, Button, FeatherIcon, Tooltip } from "frappe-ui";
import { PropType, computed, inject } from "vue";

const props = defineProps({
  activity: {
    type: Object as PropType<WhatsAppActivity>,
    required: true,
  },
});

const emit = defineEmits<{
  reply: [activity: WhatsAppActivity];
  react: [messageId: string, emoji: string];
  scrollTo: [messageId: string | undefined];
}>();

const ticket = inject(TicketSymbol);

// Delivery status casing varies across transport versions — normalize once.
const status = computed(() => (props.activity.status || "").toLowerCase());
const isOutgoing = computed(() => props.activity.direction === "Outgoing");
const isFailed = computed(() => status.value === "failed");
const isRead = computed(() => ["read", "delivered"].includes(status.value));

// A caption is the text that rides along with a media message; the transport
// stores a bare "/files/..." string when there is none, so skip that.
const hasCaption = computed(
  () => props.activity.message && !props.activity.message.startsWith("/files/")
);

const documentName = computed(
  () => props.activity.attach?.split("/").pop() || __("Document")
);

// The thread is the contact's whole conversation (omnichannel); flag the
// messages that belong to a different ticket so this ticket's own stand out.
const fromOtherTicket = computed(
  () =>
    props.activity.hd_ticket &&
    props.activity.hd_ticket !== ticket?.value?.doc?.name
);

// The reaction call is hoisted to the parent (one resource for the whole
// thread) rather than instantiated per bubble.
function onReact(emoji: string) {
  if (emoji) emit("react", props.activity.name, emoji);
}
</script>
