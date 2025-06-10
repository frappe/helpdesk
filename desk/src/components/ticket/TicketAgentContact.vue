<template>
  <div class="flex items-center justify-start gap-5 border-b p-5">
    <Avatar size="3xl" :image="contact.image" :label="contact.name" />
    <div class="flex items-center justify-between flex-1">
      <Tooltip :text="contact.name">
        <div class="w-[242px] truncate text-2xl font-medium">
          {{ contact.name }}
        </div>
      </Tooltip>
      <div class="flex gap-1.5">
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
import { Avatar, Tooltip } from "frappe-ui";

const props = defineProps({
  contact: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["email:open"]);

function openEmailBox() {
  emit("email:open", props.contact.email_id);
}
</script>
