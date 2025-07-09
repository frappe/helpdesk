<template>
  <div>
    <header class="flex justify-between">
      <div>
        <h1 class="text-lg font-semibold mb-1">Field Dependencies</h1>
        <p class="text-ink-gray-6 text-base">
          Dynamically control field options based on selection
        </p>
      </div>
      <Button
        label="New"
        variant="solid"
        size="sm"
        @click="$emit('update:step', 'fd')"
      >
        <template #prefix>
          <LucidePlus class="h-4 w-4 stroke-1.5" />
        </template>
      </Button>
    </header>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped></style>
