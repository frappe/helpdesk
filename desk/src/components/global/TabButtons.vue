<template>
    <div class="flex p-1 text-sm bg-gray-100 rounded-md">
      <button
        v-for="button in buttons"
        class="px-2 py-1 leading-none -all rounded"
        :class="
          modelValue === button.label
            ? 'bg-white shadow text-gray-900'
            : 'text-gray-700'
        "
        @click="$emit('update:modelValue', button.label)"
      >
        {{ button.label }}
      </button>
    </div>
  </template>
  <script>
  export default {
    name: 'TabButtons',
    props: {
      buttons: {
        type: Array,
        required: true,
      },
      modelValue: {
        type: String,
      },
    },
    emits: ['update:modelValue'],
  }
  </script>
