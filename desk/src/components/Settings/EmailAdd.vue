<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-1 justify-center -ml-[16px]">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="__('Add account')"
            size="md"
            @click="emit('update:step', 'email-list')"
            class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
          />
        </div>
      </div>
    </template>
    <template #content>
      <div class="flex flex-col gap-4">
        <div class="text-p-base font-medium text-ink-gray-8">
          {{ __("Choose your email provider") }}
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <button
            v-for="service in services"
            :key="service.name"
            type="button"
            class="flex items-center gap-3 rounded-md px-3 py-2.5 ring-1 ring-outline-gray-modals hover:bg-surface-gray-2 transition text-left"
            @click="handleSelect(service)"
          >
            <div class="flex h-7 w-7 items-center justify-center shrink-0">
              <img
                v-if="service.icon"
                :src="service.icon"
                :alt="service.name"
                class="h-6 w-6 object-contain"
              />
              <LucideMail v-else class="h-5 w-5 text-ink-gray-7" />
            </div>
            <span class="text-p-base text-ink-gray-8">{{ service.name }}</span>
          </button>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { EmailService, EmailStep } from "@/types";
import { Button } from "frappe-ui";
import { services } from "./emailConfig";
import LucideMail from "~icons/lucide/mail";

interface Emits {
  (event: "update:step", step: EmailStep, data?: { service?: string }): void;
}

const emit = defineEmits<Emits>();

function handleSelect(service: EmailService) {
  const nextStep: EmailStep =
    service.value === "Custom" ? "email-custom-setup" : "email-provider-setup";
  emit("update:step", nextStep, { service: service.value });
}
</script>
