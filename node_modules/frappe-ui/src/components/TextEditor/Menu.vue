<template>
  <div class="inline-flex px-1 py-1 bg-white">
    <div class="inline-flex items-center gap-1">
      <template v-for="button in buttons" :key="button.label">
        <div
          class="border-l w-[2px] h-4"
          v-if="button.type === 'separator'"
        ></div>
        <button
          v-else
          class="flex p-1 text-gray-800 transition-colors rounded"
          :class="button.isActive(editor) ? 'bg-gray-100' : 'hover:bg-gray-100'"
          @click="() => button.action(editor)"
          :title="button.label"
        >
          <FeatherIcon v-if="button.icon" :name="button.icon" class="w-4" />
          <span class="inline-block h-4 text-sm leading-4 min-w-[1rem]" v-else>
            {{ button.text }}
          </span>
        </button>
      </template>
    </div>
  </div>
</template>
<script>
import { FeatherIcon } from 'frappe-ui'
export default {
  name: 'TipTapMenu',
  props: ['editor', 'buttons'],
  components: { FeatherIcon },
}
</script>
