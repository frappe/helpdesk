<template>
  <ListCell class="flex-col !items-stretch gap-1.5">
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
  </ListCell>
</template>

<script setup lang="ts">
import { TextInput } from "frappe-ui";
import { ListCell } from "frappe-ui/list";
import { useId } from "vue";

defineOptions({ inheritAttrs: false });

defineProps<{ error?: string }>();
const value = defineModel<string>();
const errorId = useId();
</script>
