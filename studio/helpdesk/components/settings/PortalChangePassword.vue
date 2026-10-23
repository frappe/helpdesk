<template>
  <Button
    :label="__('Change password')"
    variant="subtle"
    @click="open = true"
  />
  <ChangePasswordModal v-if="open" v-model="open" :user="user" />
</template>

<script setup lang="ts">
// Studio finds custom blocks only under the app folder, so the desk's modal reaches the block tree through this.
import { computed, ref } from "vue";
import { Button } from "frappe-ui";
import ChangePasswordModal from "@helpdesk/shared/ChangePasswordModal.vue";
import { __ } from "@helpdesk/shared/translation";
import { useSession } from "@app/stores/session";

const open = ref(false);

const session = useSession();
const user = computed(() => session.config.value?.session_user);
</script>
