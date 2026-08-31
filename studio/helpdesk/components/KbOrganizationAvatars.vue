<template>
  <div v-if="organizations.length" class="kb-org-avatars">
    <!-- One organization has room for its name, so it gets one: a lone avatar with a
         tooltip asks the reader to hover to find out where they belong. -->
    <span v-if="alone" class="kb-org-avatars__item kb-org-avatars__solo">
      <Avatar
        class="kb-org-avatars__avatar"
        shape="circle"
        :size="size"
        :image="organizations[0].image"
        :label="organizations[0].customer_name"
      />
      <span class="kb-org-avatars__name">{{
        organizations[0].customer_name
      }}</span>
    </span>
    <template v-else>
      <span v-for="org in visible" :key="org.name" class="kb-org-avatars__item">
        <Tooltip :text="org.customer_name">
          <Avatar
            class="kb-org-avatars__avatar"
            shape="circle"
            :size="size"
            :image="org.image"
            :label="org.customer_name"
          />
        </Tooltip>
      </span>
      <span v-if="hidden.length" class="kb-org-avatars__item">
        <Tooltip :text="hiddenNames">
          <div class="kb-org-avatars__avatar kb-org-avatars__overflow">
            +{{ hidden.length }}
          </div>
        </Tooltip>
      </span>
    </template>
  </div>
</template>

<script setup lang="ts">
// The agent portal's MultipleAvatar in the same shape: overlapped circles, a name
// on hover, the tail collapsed into "+n". Spreading the stack on hover needs a
// :hover rule, which a block's inline styles can't express — hence a component.
import { Avatar, Tooltip } from "frappe-ui";
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    organizations?: { name: string; customer_name: string; image?: string }[];
    /** Past this many, the rest collapse into the "+n" chip. */
    max?: number;
    size?: string;
  }>(),
  { organizations: () => [], max: 3, size: "md" }
);

const alone = computed(() => props.organizations.length === 1);
const visible = computed(() => props.organizations.slice(0, props.max));
const hidden = computed(() => props.organizations.slice(props.max));
const hiddenNames = computed(() =>
  hidden.value.map((org) => org.customer_name).join(", ")
);
</script>

<style scoped>
/* Plain CSS: this app is outside the bench's Tailwind content globs, so the
   arbitrary ring/hover utilities helpdesk uses never compile here. */
.kb-org-avatars {
  display: flex;
  align-items: center;
}

.kb-org-avatars__item + .kb-org-avatars__item {
  margin-left: -6px;
  transition: margin-left 150ms ease;
}

/* Nothing to spread or scale when there is one — the name is already on screen. */
.kb-org-avatars__solo {
  align-items: center;
  gap: 8px;
}

.kb-org-avatars__name {
  font-size: 14px;
  line-height: 20px;
  color: var(--ink-gray-7);
}

/* Open the stack up so every organization is legible before it is hovered. */
.kb-org-avatars:hover .kb-org-avatars__item + .kb-org-avatars__item {
  margin-left: 4px;
}

.kb-org-avatars__item {
  display: flex;
}

.kb-org-avatars__avatar {
  box-shadow: 0 0 0 2px var(--surface-base);
  transition: transform 150ms ease;
}

.kb-org-avatars__item:not(.kb-org-avatars__solo):hover .kb-org-avatars__avatar {
  transform: scale(1.1);
}

.kb-org-avatars__overflow {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 24px; /* frappe-ui Avatar md */
  height: 24px;
  border-radius: 9999px;
  background: var(--surface-gray-3);
  color: var(--ink-gray-7);
  font-size: 12px;
}
</style>
