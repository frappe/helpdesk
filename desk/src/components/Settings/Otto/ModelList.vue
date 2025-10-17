<template>
  <div class="w-full">
    <!-- Header -->
    <div
      class="grid grid-cols-12 items-center gap-4 py-3 text-sm font-medium text-gray-600 border-b border-gray-200 sticky top-0 bg-white"
    >
      <div class="col-span-5" title="Model name">Model</div>
      <div
        class="col-span-3"
        title="Larger models are more powerful but slower and more expensive"
      >
        Size
      </div>
      <div class="col-span-2 text-center" title="Model supports reasoning">
        Reasoning
      </div>
      <div
        class="col-span-2 text-center"
        title="Model is available if the API key is set for the provider"
      >
        Available
      </div>
    </div>

    <!-- Model Items -->
    <template
      v-for="(model, index) in models
        .filter((model) => model.is_enabled)
        .sort((a, b) => a.provider.localeCompare(b.provider))"
      :key="model.name"
    >
      <div
        class="grid grid-cols-12 items-center gap-4 pt-3 hover:bg-gray-50 transition-colors -mx-2 px-2 rounded"
      >
        <!-- Model Title -->
        <div class="col-span-5 text-base font-medium text-ink-gray-7">
          {{ model.title }}
        </div>

        <!-- Size -->
        <div class="col-span-3 text-sm text-ink-gray-7">
          {{ model.size || "-" }}
        </div>

        <!-- Reasoning -->
        <div
          class="col-span-2 text-center inline-flex items-center justify-center w-full h-4 text-sm font-bold text-ink-gray-7"
        >
          {{ model.is_reasoning ? "✓" : "✕" }}
        </div>

        <!-- Available -->
        <div
          class="col-span-2 text-center inline-flex items-center justify-center w-full h-4 text-sm font-bold text-ink-gray-7"
        >
          {{ model.is_api_key_set ? "✓" : "✕" }}
        </div>
        <hr class="col-span-12 border-gray-200" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
defineProps<{ models: Record<string, any>[] }>();
</script>
