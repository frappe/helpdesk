<template>
  <component
    :is="isExternal ? 'a' : 'router-link'"
    v-bind="attributes"
    class="text-blue-500 cursor-pointer hover:text-blue-600"
  >
    <slot></slot>
  </component>
</template>

<script>
export default {
  props: ['to'],
  computed: {
    attributes() {
      return {
        ...this.$attrs,
        target: this.isExternal ? '_blank' : null,
        to: !this.isExternal ? this.to : undefined,
        href: this.isExternal ? this.to : undefined,
      }
    },
    isExternal() {
      return this.to.startsWith('http')
    },
  },
}
</script>
