<template>
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
  <SettingsLinkTable
    v-model="footer.socials"
    :title="__('Social links')"
    :description="__('Icons appear under your tagline.')"
  />
</template>

<script setup lang="ts">
import { SettingsRow, Textarea, TextInput } from "frappe-ui";
import type { KnowledgeBaseFooter } from "../knowledgeBaseFooter";
import { __ } from "../translation";
import FooterColumns from "./FooterColumns.vue";
import SettingsLinkTable from "./SettingsLinkTable.vue";

const footer = defineModel<KnowledgeBaseFooter>({ required: true });
</script>
