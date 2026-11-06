<template>
  <Dialog
    :open="open"
    bare
    size="md"
    @update:open="(value) => !value && emit('close', null)"
  >
    <div
      class="overflow-hidden rounded-6"
      role="group"
      :aria-label="__('You\'re all set')"
    >
      <div class="space-y-5 bg-surface-elevation-2 p-6">
        <div class="space-y-1.5 text-center">
          <h2 class="text-2xl-semibold text-ink-gray-9">{{ __("You're all set") }}</h2>
          <p class="text-p-base text-ink-gray-6">
            {{ __("You can change any of this later from Settings.") }}
          </p>
        </div>

        <div
          class="flex flex-col items-center gap-2 border-t border-outline-gray-1 pt-5"
        >
          <p class="text-base-medium text-ink-gray-7">
            {{ __("How was setting up Helpdesk?") }}
          </p>
          <Rating v-model="rating" />
        </div>

        <!-- Words are only asked for once they have rated -->
        <div
          class="grid transition-[grid-template-rows,opacity] duration-500 ease-out motion-reduce:transition-none"
          :class="rating ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        >
          <div class="min-h-0 overflow-hidden">
            <FormControl
              v-model="comment"
              type="textarea"
              :label="__('Anything we could improve? (optional)')"
              :rows="3"
              :maxlength="MAX_COMMENT"
              :disabled="!rating"
            />
            <p
              v-if="comment.length"
              class="mt-1 text-right text-xs tabular-nums text-ink-gray-5"
            >
              {{ comment.length }}/{{ MAX_COMMENT }}
            </p>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <Button
            variant="outline"
            :label="__('Not now')"
            @click="emit('close', null)"
          />
          <Button
            variant="solid"
            theme="gray"
            :label="__('Submit')"
            :disabled="!rating"
            @click="emit('close', { rating, comment: comment.trim() })"
          />
        </div>
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Button, Dialog, FormControl, Rating } from "frappe-ui";
import { ref } from "vue";

const MAX_COMMENT = 500;

defineProps<{ open: boolean }>();
const emit = defineEmits<{
  close: [feedback: { rating: number; comment: string } | null];
}>();

const rating = ref(0);
const comment = ref("");
</script>
