<template>
  <div class="flex items-center gap-3">
    <Avatar :label="contact.data?.name" :image="contactImage" size="2xl" />
    <div class="flex min-w-0 flex-1 flex-col gap-1.5">
      <Tooltip :text="contact.data?.name || contact.data?.email_id">
        <div class="flex items-center gap-1.5">
          <p class="truncate text-lg font-medium text-ink-gray-8">
            {{ contact.data?.name || contact.data?.email_id }}
          </p>
          <ExternalLinkIcon
            v-if="!contact.loading"
            class="size-4 shrink-0 cursor-pointer text-ink-gray-6"
            @click="openContact(contact.data.name)"
          />
        </div>
      </Tooltip>
      <div class="flex items-center gap-1 text-base text-ink-gray-5">
        <span
          class="cursor-copy"
          @click="
            copyToClipboard(
              ticket.doc.name,
              `Ticket #${ticket.doc.name} copied to clipboard`
            )
          "
        >
          #{{ ticket.doc.name }}
        </span>
        <span>via</span>
        <GlobeIcon v-if="ticket.doc.via_customer_portal" class="size-4" />
        <EmailIcon v-else class="size-4" />
        <span>{{
          ticket.doc.via_customer_portal ? __("Portal") : __("Email")
        }}</span>
      </div>
    </div>
    <Tooltip v-if="isCallingEnabled" :text="__('Call contact')">
      <Button variant="ghost" @click="callContact">
        <template #icon>
          <PhoneIcon class="size-4" />
        </template>
      </Button>
    </Tooltip>
    <SetContactPhoneModal
      v-model="showPhoneModal"
      :name="contact.data?.name ?? ''"
      @onUpdate="contact.reload"
    />
  </div>
</template>

<script setup lang="ts">
import { useShortcut } from "@/composables/shortcuts";
import { useTelephonyStore } from "@/stores/telephony";
import { useUserStore } from "@/stores/user";
import { TicketContactSymbol, TicketSymbol } from "@/types";
import { copyToClipboard, openContact } from "@/utils";
import { Avatar, Button, Tooltip } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, inject, ref } from "vue";
import { ExternalLinkIcon } from "../icons";
import EmailIcon from "../icons/EmailIcon.vue";
import GlobeIcon from "../icons/GlobeIcon.vue";
import PhoneIcon from "../icons/PhoneIcon.vue";
import SetContactPhoneModal from "../ticket/SetContactPhoneModal.vue";

const telephonyStore = useTelephonyStore();
const { getUser } = useUserStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);
const showPhoneModal = ref(false);

const ticket = inject(TicketSymbol)!;

const contact = inject(TicketContactSymbol)!;
const contactImage = computed(() => {
  if (!contact.value?.data) return "";
  const email = contact.value?.data?.email_id ?? "";
  return (
    contact.value?.data?.image || (email && getUser(email)?.user_image) || ""
  );
});

const callContact = () => {
  if (!contact.value.data.mobile_no && !contact.value.data.phone) {
    showPhoneModal.value = true;
    return;
  }
  telephonyStore.makeCall({
    number: contact.value.data.mobile_no || contact.value.data.phone,
    doctype: "HD Ticket",
    docname: ticket.value.name,
  });
};

useShortcut({ meta: true, shift: true, key: "." }, () => {
  copyToClipboard(window.location.href, `Ticket URL copied to clipboard`);
});

useShortcut({ meta: true, key: "." }, () => {
  copyToClipboard(
    ticket.value.doc.name,
    `Ticket #${ticket.value.doc.name} copied to clipboard`
  );
});
</script>
