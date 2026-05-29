<template>
  <div class="flex flex-col items-center gap-5 my-auto px-[110px] py-10">
    <EmptyState
      :title="__('No email accounts')"
      :description="__('Pick a provider below to get started.')"
      :icon="MailPlus"
      variant="badge"
      class="!static"
    />
    <div
      class="flex flex-wrap justify-center gap-2 max-w-lg pointer-events-auto"
    >
      <Button
        v-for="service in services"
        :key="service.value"
        variant="outline"
        class="px-2.5 h-auto !gap-1.5 min-w-[156px] !flex !justify-start"
        theme="gray"
        @click="emit('select', service.value)"
      >
        <template #prefix>
          <img
            v-if="service.icon"
            :src="service.icon"
            :alt="service.name"
            class="h-6 w-6 object-contain my-2.5 shrink-0"
          />
          <div v-else class="flex h-7 w-7 items-center justify-center shrink-0">
            <LucideMail class="h-5 w-5 text-ink-gray-7" />
          </div>
        </template>
        <template #suffix>
          <p class="text-p-base text-ink-gray-7 my-2.5">{{ service.name }}</p>
        </template>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import EmptyState from "./EmptyState.vue";
import LucideMail from "~icons/lucide/mail";
import MailPlus from "~icons/lucide/mail-plus";
import { services } from "./Settings/emailConfig";

const emit = defineEmits<{
  (event: "select", service: string): void;
}>();
</script>

<style lang="scss" scoped></style>
