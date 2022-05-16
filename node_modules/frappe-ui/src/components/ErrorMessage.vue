<template>
  <div
    v-if="message"
    class="text-sm text-red-600 whitespace-pre-line"
    role="alert"
    v-html="message"
  ></div>
</template>

<script>
export default {
  name: 'ErrorMessage',
  props: ['message'],
}
</script>
