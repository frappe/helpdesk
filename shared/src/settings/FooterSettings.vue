<template>
  <SettingsRow
    label-for=""
    :title="__('Show footer')"
    :description="
      __('A footer will appear at the bottom of every knowledge base page.')
    "
  >
    <Switch v-model="footer.enabled" :aria-label="__('Show footer')" />
  </SettingsRow>
  <template v-if="footer.enabled">
    <SettingsRow
      :title="__('Tagline')"
      :description="__('Short line under your logo.')"
    >
      <div class="w-72">
        <Textarea v-model="footer.tagline" :rows="3" class="max-h-40" />
      </div>
    </SettingsRow>
    <SettingsRow
      :title="__('Copyright')"
      :description="__('Shown at the bottom of the footer.')"
    >
      <TextInput
        v-model="footer.copyright"
        class="w-72"
        :placeholder="__('© 2026 Your company')"
      />
    </SettingsRow>
    <FooterColumns v-model="footer.columns" />
    <LinkTable
      v-model="footer.socials"
      :title="__('Social links')"
      :description="__('Icons appear under your tagline.')"
    />
  </template>
</template>

<script setup lang="ts">
import { SettingsRow, Switch, Textarea, TextInput } from "frappe-ui";
import type { KnowledgeBaseFooter } from "../knowledgeBaseFooter";
import { __ } from "../translation";
import FooterColumns from "./FooterColumns.vue";
import LinkTable from "./LinkTable.vue";

const footer = defineModel<KnowledgeBaseFooter>({ required: true });
</script>
