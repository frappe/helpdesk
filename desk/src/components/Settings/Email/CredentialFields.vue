<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <FormControl
      v-model="state.email_id"
      :label="__('Email')"
      type="email"
      placeholder="johndoe@example.com"
    />

    <template v-if="isOAuth">
      <FormControl
        v-model="state.client_id"
        :label="__('Client ID')"
        type="text"
        :placeholder="__('OAuth Client ID')"
      />
      <FormControl
        v-model="state.client_secret"
        :label="__('Client Secret')"
        type="password"
        placeholder="••••••••••••"
      />
    </template>

    <template v-else-if="isFrappeMail">
      <FormControl
        v-model="state.api_key"
        :label="__('API Key')"
        type="text"
        placeholder="••••••••••••"
      />
      <FormControl
        v-model="state.api_secret"
        :label="__('API Secret')"
        type="password"
        placeholder="••••••••••••"
      />
      <FormControl
        v-model="state.frappe_mail_site"
        :label="__('Frappe Mail site')"
        type="text"
        placeholder="https://frappemail.com"
      />
    </template>

    <FormControl
      v-else
      v-model="state.password"
      :label="__('Password')"
      type="password"
      placeholder="••••••••••••"
    />

    <FormControl
      v-model="state.email_account_name"
      :label="__('Account name')"
      type="text"
      :placeholder="accountNamePlaceholder"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { FormControl } from "frappe-ui";
import type { ProviderFormState } from "./providerForm";

interface Props {
  state: ProviderFormState;
  isOAuth: boolean;
  isFrappeMail: boolean;
  accountNamePlaceholder: string;
}

defineProps<Props>();
</script>
