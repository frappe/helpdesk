<template>
  <Dialog v-model="show" :options="{ title: __('Export') }">
    <template #body-content>
      <FormControl
        v-model="form.export_type"
        variant="outline"
        :label="__('Export Type')"
        type="select"
        :options="[
          {
            label: __('Excel'),
            value: 'Excel',
          },
          {
            label: __('CSV'),
            value: 'CSV',
          },
        ]"
        :placeholder="__('Excel')"
      />

      <div class="mt-3">
        <FormControl
          v-model="form.export_all"
          type="checkbox"
          :label="__('Export All {0} Record(s)', [rowCount])"
        />
      </div>
    </template>
    <template #actions>
      <Button
        :label="__('Download')"
        variant="solid"
        @click="() => emit('update', form)"
        class="w-full"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { reactive } from "vue";
import { __ } from "@/translation";

defineProps<{
  rowCount: number;
}>();

interface R {
  export_type: "CSV" | "Excel";
  export_all: boolean;
}

interface E {
  (event: "update", value: R);
}

const emit = defineEmits<E>();

const show = defineModel();

const form: R = reactive({
  export_type: "Excel",
  export_all: false,
});
</script>

<style scoped></style>
