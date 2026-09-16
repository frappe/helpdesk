<template>
  <div v-if="organizations.length" class="group flex items-center">
    <!-- One organization has room for its name, so it gets one rather than a tooltip. -->
    <span v-if="alone" class="flex items-center gap-2">
      <Avatar
        :class="RING"
        shape="square"
        :size="size"
        :image="organizations[0].image"
        :label="organizations[0].customer_name"
      />
      <span class="text-p-base text-ink-gray-7">{{
        organizations[0].customer_name
      }}</span>
    </span>
    <template v-else>
      <span v-for="org in visible" :key="org.name" :class="ITEM">
        <Tooltip :text="org.customer_name">
          <Avatar
            :class="[RING, POP]"
            shape="square"
            :size="size"
            :image="org.image"
            :label="org.customer_name"
          />
        </Tooltip>
      </span>
      <span v-if="hidden.length" :class="ITEM">
        <Tooltip :text="hiddenNames">
          <!-- size-6 matches frappe-ui's Avatar md. -->
          <div
            class="flex size-6 shrink-0 items-center justify-center rounded-[5px] bg-surface-gray-3 text-p-xs text-ink-gray-7"
            :class="[RING, POP]"
          >
            +{{ hidden.length }}
          </div>
        </Tooltip>
      </span>
    </template>
  </div>
</template>

<script setup lang="ts">
// A component because spreading on hover needs a :hover rule, which inline styles cannot.
import { Avatar, Tooltip } from "frappe-ui";
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    organizations?: { name: string; customer_name: string; image?: string }[];
    // Past this many, the rest collapse into the "+n" chip.
    max?: number;
    size?: string;
  }>(),
  { organizations: () => [], max: 3, size: "md" }
);

// `[&+&]` is the sibling combinator: each avatar after the first tucks under its neighbour.
const ITEM =
  "flex [&+&]:-ml-1.5 [&+&]:transition-[margin-left] [&+&]:duration-150 group-hover:[&+&]:ml-1";
const RING = "shadow-[0_0_0_2px_var(--surface-base)]";
const POP = "transition-transform duration-150 hover:scale-110";

const alone = computed(() => props.organizations.length === 1);
const visible = computed(() => props.organizations.slice(0, props.max));
const hidden = computed(() => props.organizations.slice(props.max));
const hiddenNames = computed(() =>
  hidden.value.map((org) => org.customer_name).join(", ")
);
</script>
