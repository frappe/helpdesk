<template>
  <div ref="reference">
    <div
      class="h-full"
      ref="target"
      @click="updatePosition"
      @focusin="updatePosition"
      @keydown="updatePosition"
    >
      <slot
        name="target"
        v-bind="{ togglePopover, updatePosition, open, close }"
      ></slot>
    </div>
    <teleport to="#frappeui-popper-root">
      <div
        ref="popover"
        :class="popoverClass"
        class="relative z-[100] popover-container"
        :style="{ minWidth: targetWidth ? targetWidth + 'px' : null }"
      >
        <div v-if="!hideArrow" class="popover-arrow" ref="popover-arrow"></div>
        <slot
          name="content"
          v-bind="{ togglePopover, updatePosition, open, close }"
        ></slot>
      </div>
    </teleport>
  </div>
</template>

<script>
import { createPopper } from '@popperjs/core'

export default {
  name: 'Popover',
  props: {
    hideArrow: {
      type: Boolean,
      default: true,
    },
    show: {
      default: null,
    },
    right: Boolean,
    placement: {
      type: String,
      default: 'bottom-start',
    },
    popoverClass: [String, Object, Array],
  },
  emits: ['init', 'open', 'close'],
  watch: {
    show: {
      immediate: true,
      handler(val) {
        if (val) {
          this.open()
        } else {
          this.close()
        }
      },
    },
  },
  data() {
    return {
      isOpen: false,
      targetWidth: null,
    }
  },
  created() {
    if (!document.getElementById('frappeui-popper-root')) {
      const root = document.createElement('div')
      root.id = 'frappeui-popper-root'
      document.body.appendChild(root)
    }
  },
  mounted() {
    this.listener = (e) => {
      let $els = [this.$refs.reference, this.$refs.popover]
      let insideClick = $els.some(
        ($el) => $el && (e.target === $el || $el.contains(e.target))
      )
      if (insideClick) {
        return
      }
      this.close()
    }
    if (this.show == null) {
      document.addEventListener('click', this.listener)
    }
    this.$nextTick(() => {
      this.targetWidth = this.$refs['target'].clientWidth
    })
  },
  beforeDestroy() {
    this.popper && this.popper.destroy()
    document.removeEventListener('click', this.listener)
  },
  methods: {
    setupPopper() {
      if (!this.popper) {
        this.popper = createPopper(this.$refs.reference, this.$refs.popover, {
          placement: this.placement,
          modifiers: !this.hideArrow
            ? [
                {
                  name: 'arrow',
                  options: {
                    element: this.$refs['popover-arrow'],
                  },
                },
                {
                  name: 'offset',
                  options: {
                    offset: [0, 10],
                  },
                },
              ]
            : [],
        })
      } else {
        this.updatePosition()
      }
      this.$emit('init')
    },
    updatePosition() {
      this.popper && this.popper.update()
    },
    togglePopover(flag) {
      if (flag == null) {
        flag = !this.isOpen
      }
      flag = Boolean(flag)
      if (flag) {
        this.open()
      } else {
        this.close()
      }
    },
    open() {
      if (this.isOpen) {
        return
      }
      this.isOpen = true
      this.$nextTick(() => this.setupPopper())
      this.$emit('open')
    },
    close() {
      if (!this.isOpen) {
        return
      }
      this.isOpen = false
      this.$emit('close')
    },
  },
}
</script>
<style scoped>
.popover-arrow,
.popover-arrow::after {
  position: absolute;
  width: theme('spacing.4');
  height: theme('spacing.4');
  z-index: -1;
}

.popover-arrow::after {
  content: '';
  background: white;
  transform: rotate(45deg);
  border-top: 1px solid theme('borderColor.gray.400');
  border-left: 1px solid theme('borderColor.gray.400');
  border-top-left-radius: 6px;
}

.popover-container[data-popper-placement^='top'] > .popover-arrow {
  bottom: calc(theme('spacing.2') * -1);
}

.popover-container[data-popper-placement^='bottom'] > .popover-arrow {
  top: calc(theme('spacing.2') * -1);
}

.popover-container[data-popper-placement^='left'] > .popover-arrow {
  right: calc(theme('spacing.2') * -1);
}

.popover-container[data-popper-placement^='right'] > .popover-arrow {
  left: calc(theme('spacing.2') * -1);
}
</style>
