<template>
  <div
    v-if="!contact.loading"
    class="my-4 flex items-center justify-start gap-5"
  >
    <Avatar :label="contact.data.name" :image="contactImage" size="2xl" />
    <div class="flex flex-col gap-1.5">
      <Tooltip :text="contact.data.name || contact.data.email_id">
        <div class="flex gap-2.5 items-center">
          <p class="text-ink-gray-8 font-medium text-xl max-w-[170px] truncate">
            {{ contact.data.name || contact.data.email_id }}
          </p>
          <ExternalLinkIcon
            class="size-4 text-ink-gray-6 cursor-pointer"
            @click="openContact(contact.data.name)"
          />
        </div>
      </Tooltip>
      <div class="flex gap-1.5">
        <Tooltip :text="contact.data.email_id">
          <!-- Email Button -->
          <Button size="sm" @click="toggleEmailBox()">
            <template #icon>
              <EmailIcon class="size-4" />
            </template>
          </Button>
          <!-- Call Button -->
          <Button size="sm" v-if="isCallingEnabled" @click="callContact">
            <template #icon>
              <PhoneIcon class="size-4" />
            </template>
          </Button>
        </Tooltip>
      </div>
    </div>
    <SetContactPhoneModal
      v-model="showPhoneModal"
      :name="contact.data.name"
      @onUpdate="contact.reload"
    />
  </div>
</template>

<script setup lang="ts">
import { toggleEmailBox } from "@/pages/ticket/modalStates";
import { useTelephonyStore } from "@/stores/telephony";
import { useUserStore } from "@/stores/user";
import { TicketContactSymbol, TicketSymbol } from "@/types";
import { Avatar, Button, Tooltip } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, inject, ref } from "vue";
import { ExternalLinkIcon } from "../icons";
import EmailIcon from "../icons/EmailIcon.vue";
import PhoneIcon from "../icons/PhoneIcon.vue";
import SetContactPhoneModal from "../ticket/SetContactPhoneModal.vue";

const telephonyStore = useTelephonyStore();
const { getUser } = useUserStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);
const showPhoneModal = ref(false);

const ticket = inject(TicketSymbol);

const contact = inject(TicketContactSymbol);
const contactImage = computed(() => {
  return (
    contact.value?.data?.image ||
    getUser(contact.value?.data?.email_id)?.user_image ||
    null
  );
});

function openContact(name: string) {
  let url = window.location.origin + "/app/contact/" + name;
  window.open(url, "_blank");
}

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
</script>

<style scoped></style>
