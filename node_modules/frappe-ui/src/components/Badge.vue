<template>
  <span
    class="inline-block px-3 py-1 text-xs font-medium rounded-md cursor-default"
    :class="classes"
  >
    <slot>{{ status }}</slot>
  </span>
</template>
<script>
export default {
  name: 'Badge',
  props: ['color', 'status'],
  computed: {
    classes() {
      let color = this.color
      if (!color && this.status) {
        color = {
          Pending: 'yellow',
          Running: 'yellow',
          Success: 'green',
          Failure: 'red',
          Active: 'green',
          Broken: 'red',
          Updating: 'blue',
          Rejected: 'red',
          Published: 'green',
          Approved: 'green',
        }[this.status]
      }
      return {
        gray: 'text-gray-700 bg-gray-50',
        green: 'text-green-700 bg-green-50',
        red: 'text-red-700 bg-red-50',
        yellow: 'text-yellow-700 bg-yellow-50',
        blue: 'text-blue-700 bg-blue-50',
      }[color || 'gray']
    },
  },
}
</script>
