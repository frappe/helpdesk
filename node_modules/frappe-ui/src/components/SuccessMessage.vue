<template>
  <div
    v-if="message"
    class="text-sm text-green-600 whitespace-pre-line"
    role="success"
    v-html="message"
  ></div>
</template>

<script>
export default {
  name: 'SuccessMessage',
  props: ['message'],
}
</script>
