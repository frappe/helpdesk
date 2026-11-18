<template>
  <Dialog v-model:open="show" :title="__('WhatsApp Templates')" size="4xl">
    <template #default>
      <TemplateSelector
        reference-doctype="HD Ticket"
        :reference-docname="ticket"
        :to="to ?? undefined"
        :filters="{ name: ['in', allowed] }"
        @sent="onSent"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { TemplateSelector } from "@whatsapp/ui";
import { Dialog } from "frappe-ui";

defineProps<{
  ticket: string;
  to?: string | null;
  /** names of the templates the ticket's Business Number may send */
  allowed: string[];
}>();
const emit = defineEmits<{ sent: [] }>();
const show = defineModel<boolean>({ default: false });

function onSent() {
  show.value = false;
  emit("sent");
}
</script>
