<template>
  <Dialog v-model:open="show" :title="title">
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <Select
          v-model="access"
          :aria-label="__('General access')"
          class="w-full"
          size="md"
          :options="accessOptions"
          :placeholder="__('Mixed')"
        />
        <!-- A new option's note can differ in length: the box eases to the
             new height while the text rises in, as in Move To. -->
        <div
          class="overflow-hidden transition-[height] duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)] motion-reduce:transition-none"
          :style="noteHeight ? { height: `${noteHeight}px` } : undefined"
          aria-live="polite"
        >
          <div ref="note">
            <Transition
              enter-from-class="translate-y-1 opacity-0 blur-[2px]"
              enter-active-class="transition-[opacity,transform,filter] duration-300 delay-100 ease-out motion-reduce:transition-none"
            >
              <div :key="access ?? ''">
                <slot :access="access" />
              </div>
            </Transition>
          </div>
        </div>
      </div>

      <div class="flex justify-end">
        <Button
          variant="solid"
          :label="actionLabel"
          :disabled="!access || (requireChange && access === visibility)"
          @click="publish"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, Dialog, Select } from "frappe-ui";
import { computed, ref, watch } from "vue";
import { useElementSize } from "@vueuse/core";
import { categoryAccess } from "@helpdesk/shared/settings/categoryAccess.ts";
import { __ } from "@/translation";

// null: the category's articles differ in access.
const props = defineProps<{
  title: string;
  visibility: string | null;
  actionLabel: string;
  requireChange?: boolean;
}>();
const emit = defineEmits<{ publish: [visibility: string] }>();
const show = defineModel<boolean>({ default: false });

// Same labels as the access column.
const accessOptions = computed(() => {
  const meta = categoryAccess();
  return ["Public", "Private", "Customers"].map((value) => ({
    value,
    label: meta[value].label,
    icon: meta[value].icon,
  }));
});

const access = ref(props.visibility);
const note = ref<HTMLElement | null>(null);
// 0 until measured: the box opens at its natural height, not from zero.
const { height: noteHeight } = useElementSize(note);

watch(show, (open) => {
  if (open) access.value = props.visibility;
});

function publish() {
  emit("publish", access.value!);
  show.value = false;
}
</script>
