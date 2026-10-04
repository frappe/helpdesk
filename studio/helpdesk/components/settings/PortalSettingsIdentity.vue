<template>
  <div class="flex items-center gap-4 pt-1.5">
    <div class="group relative size-16 shrink-0">
      <!-- Avatar's size enum stops at 46px, so the block sizes it itself. -->
      <Avatar class="size-16" :image="image" :label="name" :shape="shape" />
      <Tooltip
        v-if="editable"
        :hover-delay="0"
        side="bottom"
        :text="uploadLabel"
      >
        <button
          type="button"
          class="absolute inset-0 cursor-pointer"
          :class="shape === 'square' ? 'rounded-5' : 'rounded-full'"
          :aria-label="uploadLabel"
          @click="emit('upload')"
        />
      </Tooltip>
      <button
        v-if="image && editable"
        type="button"
        :aria-label="__('Remove photo')"
        class="absolute -right-1 -top-1 flex size-4 cursor-pointer items-center justify-center rounded-full bg-surface-base opacity-0 outline outline-black/5 duration-300 ease-in-out group-hover:opacity-100 hover:bg-surface-gray-2 before:absolute before:-inset-2 before:content-[''] [@media(hover:none)]:opacity-100"
        @click.stop="emit('remove')"
      >
        <Icon icon="lucide-x" class="size-3.5 text-ink-gray-4" />
      </button>
    </div>

    <div class="flex min-w-0 flex-col gap-1">
      <div class="flex min-h-7 items-center gap-1">
        <template v-if="!isEditing">
          <span class="min-w-0 break-words text-2xl-semibold text-ink-gray-8">{{
            name
          }}</span>
          <Button
            v-if="editable"
            class="relative !h-5 shrink-0 !px-1 before:absolute before:-inset-1.5 before:content-['']"
            variant="ghost"
            :aria-label="__('Edit name')"
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
            @keydown.enter="saveName"
            @keydown.esc.stop="isEditing = false"
          />
          <Button
            variant="outline"
            icon="lucide-check"
            :aria-label="__('Save name')"
            :loading="busy"
            @click="saveName"
          />
        </template>
      </div>
      <span class="text-p-sm text-ink-gray-6">{{ subtitle }}</span>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { Avatar, Button, Icon, TextInput, Tooltip } from "frappe-ui";
import LucideSquarePen from "~icons/lucide/square-pen";
import { __ } from "@helpdesk/shared/translation";

const props = withDefaults(
  defineProps<{
    name?: string;
    subtitle?: string;
    image?: string;
    shape?: "circle" | "square";
    maxLength?: number;
    busy?: boolean;
    editable?: boolean;
  }>(),
  { shape: "circle", editable: true }
);

const emit = defineEmits<{
  (e: "upload"): void;
  (e: "remove"): void;
  (e: "rename", value: string): void;
}>();

const uploadLabel = computed(() =>
  props.image ? __("Change photo") : __("Upload photo")
);

const isEditing = ref(false);
const draft = ref("");
const nameInput = ref<InstanceType<typeof TextInput> | null>(null);

function startEditing() {
  draft.value = props.name || "";
  isEditing.value = true;
  nextTick(() => nameInput.value?.focus());
}

function saveName() {
  const value = draft.value.trim();
  isEditing.value = false;
  if (value && value !== props.name) emit("rename", value);
}
</script>
