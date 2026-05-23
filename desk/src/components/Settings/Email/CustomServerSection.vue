<template>
  <section class="flex flex-col gap-4">
    <div
      class="border-b border-outline-gray-modals pb-2 text-p-base font-medium text-ink-gray-8"
    >
      {{ title }}
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <FormControl
        v-model="server"
        :label="serverLabel"
        type="text"
        :placeholder="serverPlaceholder"
      />
      <div class="flex flex-col gap-1">
        <FormControl
          v-model="port"
          :label="portLabel"
          type="text"
          :placeholder="portPlaceholder"
        />
        <p class="text-p-sm text-ink-gray-5 flex items-center gap-1">
          <LucideInfo class="h-3.5 w-3.5" />
          {{ portHint }}
        </p>
      </div>
      <FormControl
        v-model="login"
        :label="__('Login')"
        type="text"
        :placeholder="__('support@yourcompanydomain.com')"
      />
      <FormControl
        v-model="password"
        :label="__('Password')"
        type="password"
        :placeholder="__('Enter your password')"
      />
    </div>
    <div class="flex flex-col gap-3">
      <label class="flex items-center gap-2">
        <FormControl v-model="useSsl" type="checkbox" />
        <span class="text-p-sm text-ink-gray-7">
          {{ __("Connect with SSL/TLS Encryption") }}
        </span>
        <Badge
          variant="subtle"
          class="!bg-surface-violet-1 text-ink-violet-1"
          :label="__('Enable enhanced security')"
        >
          <template #prefix>
            <LucideShieldCheck class="h-3 w-3 text-ink-violet-1" />
          </template>
        </Badge>
      </label>
      <slot name="extras" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Badge, FormControl } from "frappe-ui";
import LucideInfo from "~icons/lucide/info";
import LucideShieldCheck from "~icons/lucide/shield-check";

interface Props {
  title: string;
  serverLabel: string;
  serverPlaceholder: string;
  portLabel: string;
  portPlaceholder: string;
  portHint: string;
}

defineProps<Props>();

const server = defineModel<string>("server", { required: true });
const port = defineModel<string>("port", { required: true });
const login = defineModel<string>("login", { required: true });
const password = defineModel<string>("password", { required: true });
const useSsl = defineModel<boolean>("useSsl", { required: true });
</script>
