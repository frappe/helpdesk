<template>
  <!-- Stacked avatars, then the addresses on one truncated line.
       16px avatars line up with the other icon rows. -->
  <div class="flex min-w-0 flex-1 items-center gap-2">
    <div class="isolate flex shrink-0 items-center">
      <Tooltip v-for="email in visible" :key="email" :text="email">
        <Avatar
          :label="email"
          size="xs"
          class="-mr-1.5 ring-2 ring-[var(--surface-base)] transition hover:z-20 hover:scale-110 motion-reduce:transition-none"
        />
      </Tooltip>
      <Tooltip v-if="hidden.length" :text="hidden.join(', ')">
        <div
          class="relative z-10 -mr-1.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-surface-gray-3 text-2xs text-ink-gray-7 ring-2 ring-[var(--surface-base)]"
        >
          +{{ hidden.length }}
        </div>
      </Tooltip>
    </div>
    <PortalTruncatedText
      class="ms-1.5 text-base text-ink-gray-8"
      :text="emails.join(', ')"
    />
  </div>
</template>

<script setup lang="ts">
import { Avatar, Tooltip } from "frappe-ui";
import { computed } from "vue";
import PortalTruncatedText from "@app/components/ui/PortalTruncatedText.vue";

const MAX = 3;

const props = defineProps<{ emails: string[] }>();

const visible = computed(() => props.emails.slice(0, MAX));
const hidden = computed(() => props.emails.slice(MAX));
</script>
