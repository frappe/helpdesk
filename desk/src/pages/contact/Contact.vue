<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="-ml-[2px]" />
      </template>
    </LayoutHeader>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import type { DocumentResource } from "@/types";
import type { Contact } from "@/types/doctypes";
import { Breadcrumbs, createDocumentResource, usePageMeta } from "frappe-ui";

const props = defineProps<{
  id: string;
}>();

const doc: DocumentResource<Contact> = createDocumentResource({
  doctype: "Contact",
  name: props.id,
});

const breadcrumbs = [
  {
    label: __("Contacts"),
    route: { name: "ContactList" },
  },
  {
    label: props.id,
  },
];
usePageMeta(() => {
  return {
    title: `Contact: ${props.id}`,
  };
});
</script>

<style scoped></style>
