<template>
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" v-if="visible">
      <div class="bg-white rounded shadow-lg p-6 w-96 max-w-full">
        <p class="text-lg mb-4">{{ message }}</p>
        <div class="flex justify-end space-x-2">
          <button
            class="inline-flex items-center justify-center gap-2 transition-colors focus:outline-none text-white bg-gray-900 hover:bg-gray-800 active:bg-gray-700 focus-visible:ring focus-visible:ring-gray-400 h-7 text-base px-2 rounded"
            @click="cancel"
          >
            No
          </button>
          <button
            class="inline-flex items-center justify-center gap-2 transition-colors focus:outline-none text-white bg-gray-900 hover:bg-gray-800 active:bg-gray-700 focus-visible:ring focus-visible:ring-gray-400 h-7 text-base px-2 rounded"
            @click="confirm"
          >
            Yes
          </button>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      visible: { type: Boolean, required: true },
      message: { type: String, default: "Are you sure?" },
    },
    methods: {
      confirm() {
        this.$emit("confirm");
      },
      cancel() {
        this.$emit("cancel");
      },
    },
  };
  </script>
  