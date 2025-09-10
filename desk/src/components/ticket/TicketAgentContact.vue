<template>
  <div class="flex items-center justify-start gap-5 border-b p-5">
    <Avatar size="3xl" :image="contact.image" :label="contact.name" />
    <div class="flex items-center justify-between flex-1">
      <Tooltip :text="contact.name">
        <div class="w-full truncate text-2xl font-medium">
          {{ contact.name }}
        </div>
      </Tooltip>
      <div class="flex gap-1.5">
        <Tooltip :text="`Call ${contact.name}`" v-if="isCallingEnabled">
          <Button @click="callContact">
            <template #icon>
              <PhoneIcon class="size-4" />
            </template>
          </Button>
        </Tooltip>
        <Tooltip :text="contact.email_id">
          <Button @click="openEmailBox()">
            <template #icon>
              <EmailIcon class="size-4" />
            </template>
          </Button>
        </Tooltip>
        <!-- <RouterLink
          class="group cursor-pointer space-x-1 hover:text-gray-900"
          :to="{
            name: 'TicketsAgent',
          }"
          target="_blank"
        >
          <Button
            class="h-7 w-7"
            @click="
              () => {
                console.log('Show Contact Tickets');
              }
            "
          >
            <Tooltip text="Show Contact Tickets">
              <TicketIcon class="h-4 w-4" />
            </Tooltip>
          </Button>
        </RouterLink> -->
      </div>
    </div>
  </div>
  <SetContactPhoneModal
    v-model="showPhoneModal"
    :name="contact.name"
    @onUpdate="refreshTicket()"
  />
</template>

<script setup lang="ts">
import { EmailIcon, PhoneIcon } from "@/components/icons/";
import { useTelephonyStore } from "@/stores/telephony";
import { Avatar, Tooltip, Button } from "frappe-ui";
import { storeToRefs } from "pinia";
import SetContactPhoneModal from "./SetContactPhoneModal.vue";
import { inject, ref } from "vue";

const telephonyStore = useTelephonyStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);
const showPhoneModal = ref(false);
const refreshTicket = inject<() => void>("refreshTicket");

const props = defineProps({
  contact: {
    type: Object,
    required: true,
  },
  ticketId: {
    type: String,
    required: true,
  },
});

const callContact = () => {
  if (!props.contact.mobile_no && !props.contact.phone) {
    showPhoneModal.value = true;
    return;
  }
  telephonyStore.makeCall({
    number: props.contact.mobile_no || props.contact.phone,
    doctype: "HD Ticket",
    docname: props.ticketId,
  });
};
const emit = defineEmits(["email:open"]);

function openEmailBox() {
  emit("email:open", props.contact.email_id);
}
</script>
