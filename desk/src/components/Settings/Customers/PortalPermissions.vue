<template>
  <SettingsLayoutBase
    :title="__('Portal Permissions')"
    :description="
      __('Manage what customers and visitors can do on the customer portal.')
    "
  >
    <template #content>
      <PortalPermissionsForm />
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import PortalPermissionsForm from "@helpdesk/shared/settings/PortalPermissionsForm.vue";
</script>
