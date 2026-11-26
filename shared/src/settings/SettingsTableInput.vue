<template>
  <div class="-ms-2 flex w-[calc(100%+0.5rem)] flex-col gap-1.5">
    <TextInput
      v-model="value"
      v-bind="$attrs"
      :aria-errormessage="error ? errorId : undefined"
      class="peer w-full [&_input]:text-ellipsis"
      variant="ghost"
    />
    <p
      v-if="error"
      :id="errorId"
      class="hidden text-p-sm text-ink-red-5 peer-has-[:user-invalid]:block"
    >
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { TextInput } from "frappe-ui";
import { useId } from "vue";

defineOptions({ inheritAttrs: false });

defineProps<{ error?: string }>();
const value = defineModel<string>();
const errorId = useId();
</script>
