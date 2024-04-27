<template>
  <div class="flex items-center justify-start gap-5 border-b p-5">
    <Avatar size="3xl" class="h-[88px] w-[88px]" :label="name" />
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
        <Tooltip text="Go to website...">
          <Button class="h-7 w-7">
            <LinkIcon
              class="h-4 w-4"
              @click="
                website
                  ? openWebsite()
                  : errorMessage('error', 'Website not available')
              "
            />
          </Button>
        </Tooltip>
        <Tooltip text="Show Customer Tickets">
          <Button class="h-7 w-7">
            <TicketIcon class="h-4 w-4" @click="console.log('tick')" />
          </Button>
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar, Tooltip } from "frappe-ui";
import { EmailIcon, LinkIcon, TicketIcon } from "@/components/icons/";
import { errorMessage } from "@/utils";

const props = defineProps({
  name: {
    type: String,
    required: true,
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

function openWebsite() {
  console.log("Open website");
}
</script>
