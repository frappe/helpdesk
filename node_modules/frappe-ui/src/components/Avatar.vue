<template>
  <div class="overflow-hidden" :class="styleClasses">
    <img
      v-if="imageURL"
      :src="imageURL"
      class="object-cover"
      :class="styleClasses"
    />
    <div
      v-else
      class="flex items-center justify-center w-full h-full text-gray-600 uppercase bg-gray-200"
      :class="{ sm: 'text-xs', md: 'text-base', lg: 'text-lg' }[size]"
    >
      {{ label && label[0] }}
    </div>
  </div>
</template>

<script>
const validShapes = ['square', 'circle']

export default {
  name: 'Avatar',
  props: {
    imageURL: String,
    label: String,
    size: {
      default: 'md',
    },
    shape: {
      default: 'circle',
      validator(value) {
        const valid = validShapes.includes(value)
        if (!valid) {
          console.warn(
            `shape property for <Avatar /> must be one of `,
            validShapes
          )
        }
        return valid
      },
    },
  },
  computed: {
    styleClasses() {
      const sizeClasses = {
        sm: 'w-5 h-5',
        md: 'w-8 h-8',
        lg: 'w-12 h-12',
      }[this.size]

      const shapeClass = {
        circle: 'rounded-full',
        square: 'rounded-lg',
      }[this.shape]

      return `${shapeClass} ${sizeClasses}`
    },
  },
}
</script>
