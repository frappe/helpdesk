<template>
  <!-- The agent portal's Profile identity block (desk/.../Settings/Profile/Profile.vue):
       the avatar itself opens the native file picker — no intermediate dialog — and a
       hover-revealed × clears it. The name is edited inline rather than in a form. -->
  <div class="flex items-center gap-4 pt-1.5">
    <div class="group relative shrink-0" :style="avatarBox">
      <!-- Avatar's size enum stops at 46px, so both scales set it directly. -->
      <Avatar :style="avatarBox" :image="image" :label="name" :shape="shape" />
      <Tooltip
        v-if="editable"
        :hover-delay="0"
        placement="bottom"
        :text="uploadLabel"
      >
        <div
          class="absolute inset-0 cursor-pointer"
          :class="shape === 'square' ? 'rounded-md' : 'rounded-full'"
          @click="$emit('upload')"
        />
      </Tooltip>
      <div
        v-if="image && editable"
        class="absolute -right-1 -top-1 flex size-4 cursor-pointer items-center justify-center rounded-full bg-surface-base opacity-0 outline duration-300 ease-in-out group-hover:opacity-100 hover:bg-surface-gray-2"
        style="outline-color: rgb(0 0 0 / 0.05)"
        @click.stop="$emit('remove')"
      >
        <FeatherIcon name="x" class="size-3.5 text-ink-gray-4" />
      </div>
    </div>

    <div class="flex min-w-0 flex-col gap-1">
      <!-- Both states share the input's height so switching doesn't move the block. -->
      <div class="flex items-center gap-1" style="min-height: 28px">
        <template v-if="!editing">
          <span class="text-ink-gray-8" :class="titleClass">{{ name }}</span>
          <Button
            v-if="editable"
            class="!h-5"
            style="padding-inline: 4px"
            variant="ghost"
            @click="startEditing"
          >
            <LucideSquarePen class="size-3.5" />
          </Button>
        </template>
        <template v-else>
          <TextInput
            ref="nameInput"
            v-model="draft"
            :maxlength="maxLength"
            @keydown.enter="commit"
            @keydown.esc.stop="editing = false"
          />
          <Button
            variant="outline"
            icon="lucide-check"
            :loading="busy"
            @click="commit"
          />
        </template>
      </div>
      <span class="text-p-sm text-ink-gray-6">{{ subtitle }}</span>
      <!-- Anything else that belongs to the identity, aligned with the name column. -->
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar, Button, FeatherIcon, TextInput, Tooltip } from "frappe-ui";
import { computed, nextTick, ref } from "vue";
// The agent portal draws its icons from lucide; feather's pencil is a different glyph.
import LucideSquarePen from "~icons/lucide/square-pen";

const props = withDefaults(
  defineProps<{
    name?: string;
    subtitle?: string;
    image?: string;
    shape?: "circle" | "square";
    maxLength?: number;
    busy?: boolean;
    /** A read-only viewer sees the block without upload/remove/rename affordances. */
    editable?: boolean;
    /** "page" matches the agent portal's PageInfo header; "settings" is the compact one. */
    scale?: "settings" | "page";
  }>(),
  { shape: "circle", editable: true, scale: "settings" }
);

const avatarBox = computed(() => {
  const size = props.scale === "page" ? "52px" : "64px";
  return { width: size, height: size };
});

const titleClass = computed(() =>
  props.scale === "page" ? "text-2xl font-medium" : "text-md font-semibold"
);

/** Same wording the agent portal's profile shows on the avatar. */
const uploadLabel = computed(() =>
  props.image ? "Change Photo" : "Upload Photo"
);

const emit = defineEmits<{
  (e: "upload"): void;
  (e: "remove"): void;
  (e: "rename", value: string): void;
}>();

const editing = ref(false);
const draft = ref("");
const nameInput = ref<{ el?: HTMLInputElement } | null>(null);

function startEditing() {
  draft.value = props.name || "";
  editing.value = true;
  nextTick(() => nameInput.value?.el?.focus());
}

function commit() {
  const value = draft.value.trim();
  editing.value = false;
  if (value && value !== props.name) emit("rename", value);
}
</script>
