<template>
  <div class="flex items-center justify-between py-3">
    <div>
      <h3 class="text-base font-medium text-gray-900">
        {{ title }}
      </h3>
      <div class="mt-1" v-if="secondaryText || $slots.subtitle">
        <template v-if="secondaryText">
          <span class="text-base text-gray-600" v-html="secondaryText" />
        </template>
        <slot v-if="$slots.subtitle" name="subtitle" />
      </div>
    </div>
    <slot name="actions"></slot>
  </div>
</template>
<script>
export default {
  name: 'ListItem',
  props: ['title', 'subtitle'],
  computed: {
    secondaryText() {
      let text = this.subtitle || ''
      return text.replace('\n', '<br>')
    },
  },
}
</script>
