<template>
  <div
    v-if="!contact.loading"
    class="my-4 flex items-center justify-start gap-3"
  >
    <Avatar :label="contact.data.name" :image="contact.data.image" size="2xl" />
    <div class="flex flex-col gap-1.5">
      <div class="flex gap-2.5 items-center">
        <p class="text-ink-gray-8 font-medium text-xl max-w-[170px] truncate">
          {{ contact.data.name || contact.data.email_id }}
        </p>
        <ExternalLinkIcon class="size-4 text-ink-gray-6" />
      </div>
      <div class="flex gap-1.5">
        <Tooltip :text="contact.data.email_id">
          <!-- Email Button -->
          <Button size="sm">
            <template #icon>
              <EmailIcon class="size-4" @click="" />
            </template>
          </Button>
          <!-- Call Button -->
          <Button size="sm">
            <template #icon>
              <LucidePhone class="size-4" @click="" />
            </template>
          </Button>
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from "@/stores/user";
import { Avatar, Tooltip, Button } from "frappe-ui";
import EmailIcon from "../icons/EmailIcon.vue";
import { ExternalLinkIcon } from "../icons";
import { inject } from "vue";
import { TicketContactSymbol } from "@/types";

const contact = inject(TicketContactSymbol);
</script>

<style scoped></style>
