<template>
  <nav
    v-if="links?.length"
    :aria-label="__('Links')"
    class="flex items-center gap-1"
  >
    <!-- Button opens every `href` in a new tab; these attrs override it. -->
    <Button
      v-for="link in textLinks"
      :key="link.url + link.label"
      class="max-sm:hidden"
      variant="ghost"
      :label="link.label"
      :href="link.url"
      v-bind="linkTarget(link.open_in_new_tab)"
    />
    <Button
      v-for="link in iconLinks"
      :key="link.url + link.label"
      variant="ghost"
      :label="link.label"
      :tooltip="link.label"
      :href="link.url"
      v-bind="linkTarget(link.open_in_new_tab)"
    >
      <template #icon>
        <PortalServiceIcon :name="link.icon" class="size-4" />
      </template>
    </Button>
  </nav>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { linkTarget } from "@helpdesk/shared/utils";
import PortalServiceIcon from "@app/components/header/PortalServiceIcon.vue";

type HeaderLink = {
  label: string;
  url: string;
  open_in_new_tab?: number | boolean;
  icon?: string | null;
};

// URLs already vetted by useKnowledgeBaseHeader.
const props = defineProps<{ links?: HeaderLink[] }>();

const textLinks = computed(() => (props.links || []).filter((l) => !l.icon));
const iconLinks = computed(() => (props.links || []).filter((l) => l.icon));
</script>
