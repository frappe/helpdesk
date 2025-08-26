<template>
  <div v-if="contact" class="my-4 flex items-center justify-start gap-3">
    <Avatar :label="user.name" :image="user.user_image" size="2xl" />
    <div class="flex flex-col gap-1">
      <p class="text-ink-gray-8 font-medium text-2xl">
        {{ user.name || user.email }}
      </p>
      <div class="flex gap-1.5">
        <Tooltip :text="user.email_id">
          <!-- Email Button -->
          <Button class="h-7 w-7">
            <template #icon>
              <EmailIcon class="h-4 w-4" @click="" />
            </template>
          </Button>
          <!-- Call Button -->
          <Button class="h-7 w-7">
            <template #icon>
              <LucidePhone class="h-4 w-4" @click="" />
            </template>
          </Button>
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from "@/stores/user";
import { Avatar, Tooltip } from "frappe-ui";
import EmailIcon from "../icons/EmailIcon.vue";

// with contact name
const props = defineProps({
  contact: {
    type: String,
    required: true,
  },
});

const { getUser } = useUserStore();
const user = getUser(props.contact);
</script>

<style scoped></style>
