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
        <Button
          v-if="isCallingEnabled"
          class="h-7 w-7"
          icon="phone"
          @click="callContact"
        />
        <Tooltip :text="contact.email_id">
          <Button class="h-7 w-7">
            <template #icon>
              <EmailIcon class="h-4 w-4" @click="openEmailBox()" />
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
</template>

<script setup lang="ts">
import { EmailIcon } from "@/components/icons/";
import { useTelephonyStore } from "@/stores/telephony";
import { Avatar, toast, Tooltip, Button } from "frappe-ui";
import { storeToRefs } from "pinia";

const telephonyStore = useTelephonyStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);

const props = defineProps({
  contact: {
    type: Object,
    required: true,
  },
});

const callContact = () => {
  if (!props.contact.phone && !props.contact.mobile_no) {
    toast.error("Phone number not found for this contact");
    return;
  }
  telephonyStore.makeCall(props.contact.mobile_no || props.contact.phone);
};
const emit = defineEmits(["email:open"]);

function openEmailBox() {
  emit("email:open", props.contact.email_id);
}
</script>
