<template>
  <div class="flex items-center justify-start gap-5 border-b p-5">
    <UserAvatar size="3xl" class="h-[88px] w-[88px]" :name="name" />
    <div class="flex flex-col gap-2.5">
      <Tooltip :text="name">
        <div class="w-[242px] truncate text-2xl font-medium">
          {{ name }}
        </div>
      </Tooltip>
      <div class="flex gap-1.5">
        <Button class="h-7 w-7">
          <EmailIcon class="h-4 w-4" @click="openEmailBox()" />
        </Button>
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
import { Tooltip } from "frappe-ui";
import { UserAvatar } from "@/components";
import { EmailIcon, TicketIcon } from "@/components/icons/";

const props = defineProps({
  name: {
    type: String,
    required: true,
    default: "Contact not found",
  },
  email: {
    type: String,
    required: true,
  },
  website: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["email:open"]);

function openEmailBox() {
  emit("email:open", props.email);
}
</script>
