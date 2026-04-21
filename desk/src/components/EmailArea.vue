<template>
  <div
    :id="`communication-${name}`"
    v-bind="$attrs"
    class="grow cursor-pointer bg-white rounded-md text-base leading-6 transition-all duration-300 ease-in-out border border-outline-gray-2"
  >
    <div
      class="flex items-center justify-between gap-2"
      :class="isMobileView && 'items-start'"
    >
      <!-- email design for mobile -->
      <div v-if="isMobileView" class="flex items-center gap-2 text-sm">
        <div class="leading-tight">
          <p>{{ sender.full_name || "Guest" }}</p>
          <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
            <p class="text-xs md:text-sm text-ink-gray-5">
              {{ timeAgo(creation) }}
            </p>
          </Tooltip>
          <p class="sm:flex hidden text-sm text-ink-gray-5" v-if="sender.name">
            {{ "<" + sender.name + ">" }}
          </p>
        </div>
      </div>
      <!-- email design for desktop -->
      <div v-else class="flex items-center gap-1">
        <span>{{ sender.full_name || "Guest" }}</span>
        <span
          class="sm:flex hidden text-sm text-ink-gray-5"
          v-if="sender.name"
          >{{ "<" + sender.name + ">" }}</span
        >
      </div>

      <div class="flex gap-2 items-center">
        <div class="gap-0.5 flex items-center">
          <Badge
            v-if="status.label && !ticket.doc.via_customer_portal"
            :label="__(status.label)"
            variant="subtle"
            :theme="status.color"
            class="mr-1.5"
          />
          <Tooltip
            :text="dateFormat(creation, dateTooltipFormat)"
            v-if="!isMobileView"
          >
            <p class="text-xs md:text-sm text-ink-gray-5">
              {{ timeAgo(creation) }}
            </p>
          </Tooltip>
        </div>
        <div class="flex items-center gap-0.5">
          <Button
            :tooltip="__('Reply')"
            variant="ghost"
            class="text-ink-gray-7"
            :icon="ReplyIcon"
            @click="reply"
          />
          <Button
            :tooltip="__('Reply All')"
            variant="ghost"
            :icon="ReplyAllIcon"
            class="text-ink-gray-7"
            @click="replyAll"
          />
          <Dropdown
            v-if="showSplitOption"
            :placement="'right'"
            :options="[
              {
                label: 'Split Ticket',
                icon: LucideSplit,
                onClick: () => (showSplitModal = true),
              },
            ]"
          >
            <Button
              icon="more-horizontal"
              class="text-ink-gray-5 ml-0.5"
              variant="ghost"
            />
          </Dropdown>
        </div>
      </div>
    </div>
    <!-- <div class="text-sm leading-5 text-ink-gray-5">
      {{ subject }}
    </div> -->
    <div class="text-sm leading-5 text-ink-gray-5">
      <span v-if="to" class="mr-1">To:</span>
      <span v-if="to"> {{ to }} </span>
      <span v-if="cc">, </span>
      <span v-if="cc"> Cc: </span>
      <span v-if="cc">{{ cc }}</span>
      <span v-if="bcc">, </span>
      <span v-if="bcc"> Bcc: </span>
      <span v-if="bcc">{{ bcc }}</span>
    </div>
    <div class="border-0 border-t my-3 border-outline-gray-modals !-mx-3" />
    <EmailContent :content="content" />
    <div class="flex flex-wrap gap-2">
      <AttachmentItem
        v-for="a in attachments"
        :key="a.file_url"
        :label="a.file_name"
        :url="a.file_url"
      />
    </div>
  </div>
  <TicketSplitModal
    v-model="showSplitModal"
    :ticket_id="name"
    :communication_id="name"
  />
</template>

<script setup lang="ts">
import { AttachmentItem } from "@/components";
import { useScreenSize } from "@/composables/screen";
import { useAuthStore } from "@/stores/auth";
import { TicketSymbol } from "@/types";
import { dateFormat, dateTooltipFormat, timeAgo } from "@/utils";
import { Dropdown } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, inject, ref } from "vue";
import LucideSplit from "~icons/lucide/split";
import { ReplyAllIcon, ReplyIcon } from "./icons";
import TicketSplitModal from "./ticket/TicketSplitModal.vue";

const props = defineProps({
  activity: {
    type: Object,
    required: true,
  },
  showSplitOption: {
    type: Boolean,
    default: false,
  },
});

const {
  sender,
  to,
  cc,
  bcc,
  creation,
  subject,
  attachments,
  content,
  name,
  deliveryStatus,
} = props.activity;

const emit = defineEmits(["reply"]);
const ticket = inject(TicketSymbol)!;

const auth = storeToRefs(useAuthStore());

const { isMobileView } = useScreenSize();

const showSplitModal = ref(false);

const status = computed(() => {
  let _status = deliveryStatus;
  let indicator_color = "red";
  if (["Sent", "Clicked"].includes(_status)) {
    indicator_color = "green";
  } else if (["Sending", "Scheduled"].includes(_status)) {
    indicator_color = "orange";
  } else if (["Opened", "Read"].includes(_status)) {
    indicator_color = "blue";
  } else if (_status == "Error") {
    indicator_color = "red";
  }
  return { label: _status, color: indicator_color };
});

const reply = () => {
  const user = auth.user.value;
  emit("reply", {
    content: content,
    to: user === sender.name ? to : sender.name,
  });
};

const replyAll = () => {
  const user = auth.user.value;

  const normalizeAndFilter = (field) => {
    let arr = [];
    let current = "";
    let inQuotes = false;
    if (typeof field === "string") {
      for (let char of field) {
        if (char === '"') {
          inQuotes = !inQuotes;
          current += char;
        } else if (char === "," && !inQuotes) {
          arr.push(current.trim());
          current = "";
        } else {
          current += char;
        }
      }
      if (current) arr.push(current.trim());
    } else {
      arr = field || [];
    }
    return arr.filter((item) => item !== user && item !== sender.name);
  };

  const filteredTo = normalizeAndFilter(to);
  const filteredCc = normalizeAndFilter(cc);
  const filteredBcc = normalizeAndFilter(bcc);

  let _to, _cc, _bcc;

  if (user === sender.name) {
    // User is the sender, reply to all original recipients
    _to = filteredTo.join(", ");
    _cc = filteredCc;
    _bcc = filteredBcc;
  } else {
    // User is a recipient, reply to sender with all other recipients in cc
    _to = sender.name;
    _cc = [...filteredTo, ...filteredCc];
    _bcc = filteredBcc;
  }

  emit("reply", {
    content: content,
    to: _to,
    cc: _cc.filter(Boolean),
    bcc: _bcc.filter(Boolean),
  });
};

// TODO: Implement reply functionality using this way instead of emit drillup
// function reply(email, reply_all = false) {
//   emailBox.toggleEmailBox();
//   let editor = emailBox.editor;
//   let message = email.content;
//   let recipients = sender.name;
//   editor.toEmails = [email.sender];
//   editor.cc = editor.bcc = false;
//   editor.ccEmails = [];
//   editor.bccEmails = [];
//   console.log(recipients);

//   if (!email.subject.startsWith("Re:")) {
//     editor.subject = `Re: ${email.subject}`;
//   } else {
//     editor.subject = email.subject;
//   }

//   if (reply_all) {
//     let cc = email.cc?.split(",").map((r) => r.trim());
//     let bcc = email.bcc?.split(",").map((r) => r.trim());

//     if (cc?.length) {
//       recipients = recipients.filter((r) => !cc?.includes(r));
//       cc.push(...recipients);
//     } else {
//       cc = recipients;
//     }

//     editor.cc = cc ? true : false;
//     editor.bcc = bcc ? true : false;

//     editor.ccEmails = cc;
//     editor.bccEmails = bcc;
//   }

//   let repliedMessage = `<blockquote>${message}</blockquote>`;

//   editor.editor
//     .chain()
//     .clearContent()
//     .insertContent("<p>.</p>")
//     .updateAttributes("paragraph", { class: "reply-to-content" })
//     .insertContent(repliedMessage)
//     .focus("all")
//     .insertContentAt(0, { type: "paragraph" })
//     .focus("start")
//     .run();
// }
</script>

<style>
.email-content {
  max-width: 100%;
}
.email-content > * {
  display: flex;
  flex-direction: column;
  flex-wrap: nowrap;
}
</style>
