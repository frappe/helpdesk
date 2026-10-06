<template>
  <SettingsLayoutBase
    :title="__('Portal permissions')"
    :description="
      __(
        'Choose what visitors and customer managers can do from the customer portal.'
      )
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
