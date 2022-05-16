<template>
  <teleport to="#modals">
    <div
      v-show="show"
      class="fixed inset-0 flex items-center justify-center px-4 py-4"
    >
      <div
        v-show="show"
        class="fixed inset-0 transition-opacity"
        @click="onBackdropClick"
      >
        <div class="absolute inset-0 bg-gray-900 opacity-75"></div>
      </div>

      <div
        v-show="show"
        class="w-full overflow-auto transition-all transform bg-white rounded-lg shadow-xl"
        :class="!full ? 'sm:max-w-lg' : ''"
        style="max-height: 95vh"
      >
        <slot></slot>
      </div>
    </div>
  </teleport>
</template>

<script>
export default {
  name: 'Modal',
  props: {
    show: {
      type: Boolean,
      default: false,
    },
    dismissable: {
      type: Boolean,
      default: true,
    },
    full: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['change'],
  created() {
    if (!this.dismissable) return
    this.escapeListener = (e) => {
      if (e.key === 'Escape') {
        this.hide()
      }
    }
    document.addEventListener('keydown', this.escapeListener)
  },
  unmounted() {
    document.removeEventListener('keydown', this.escapeListener)
  },
  methods: {
    onBackdropClick() {
      if (!this.dismissable) return
      this.hide()
    },
    hide() {
      this.$emit('change', false)
    },
  },
}
</script>
