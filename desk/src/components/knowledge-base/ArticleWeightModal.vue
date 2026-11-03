<template>
  <Dialog
    v-model:open="open"
    :title="title"
    :actions="[{ label: __('Save'), variant: 'solid', onClick: save }]"
  >
    <template #default>
      <FormControl
        v-model="weight"
        type="number"
        min="0"
        :label="__('Weight')"
        :description="
          __(
            'A higher weight lists first in its category. Leave 0 to keep the usual order, newest first.'
          )
        "
        @keydown.enter="save"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Dialog, FormControl } from "frappe-ui";
import { computed, ref, watch } from "vue";

const props = defineProps<{
  count: number;
  // The current weight, for one article.
  initialWeight?: number;
}>();

const emit = defineEmits<{ save: [weight: number] }>();

const open = defineModel<boolean>({ required: true });
const weight = ref<number | string>(0);
const cleanWeight = computed(() => Math.max(0, Number(weight.value) || 0));

const title = computed(() =>
  props.count > 1
    ? __("Set weight for {0} articles", [props.count])
    : __("Set weight")
);

watch(open, (value) => {
  if (value) weight.value = props.initialWeight || 0;
});

function save() {
  open.value = false;
  emit("save", cleanWeight.value);
}
</script>
