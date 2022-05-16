<template>
  <TransitionRoot as="template" :show="open">
    <HDialog
      as="div"
      class="fixed inset-0 z-10 overflow-y-auto"
      @close="open = false"
    >
      <div
        class="flex items-end justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0"
      >
        <TransitionChild
          as="template"
          enter="ease-out duration-300"
          enter-from="opacity-0"
          enter-to="opacity-100"
          leave="ease-in duration-200"
          leave-from="opacity-100"
          leave-to="opacity-0"
        >
          <DialogOverlay
            class="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          />
        </TransitionChild>

        <!-- This element is to trick the browser into centering the modal contents. -->
        <span
          class="hidden sm:inline-block sm:align-middle sm:h-screen"
          aria-hidden="true"
        >
          &#8203;
        </span>
        <TransitionChild
          as="template"
          enter="ease-out duration-300"
          enter-from="opacity-0 translate-y-4 sm:-translate-y-12 sm:scale-95"
          enter-to="opacity-100 translate-y-0 sm:scale-100"
          leave="ease-in duration-200"
          leave-from="opacity-100 translate-y-0 sm:scale-100"
          leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
        >
          <div
            class="inline-block overflow-hidden text-left align-bottom transition-all transform bg-white rounded-lg shadow-xl sm:my-8 sm:align-middle sm:max-w-lg sm:w-full"
          >
            <slot name="body">
              <slot name="body-main">
                <div class="px-4 py-5 bg-white sm:p-6">
                  <div class="flex flex-col sm:flex-row">
                    <div
                      v-if="icon"
                      class="flex items-center justify-center flex-shrink-0 w-12 h-12 mx-auto mb-3 rounded-full sm:mx-0 sm:h-9 sm:w-9 sm:mb-0 sm:mr-4"
                      :class="{
                        'bg-yellow-100': icon.appearance === 'warning',
                        'bg-blue-100': icon.appearance === 'info',
                        'bg-red-100': icon.appearance === 'danger',
                        'bg-green-100': icon.appearance === 'success',
                      }"
                    >
                      <FeatherIcon
                        :name="icon.name"
                        class="w-6 h-6 text-red-600 sm:w-5 sm:h-5"
                        :class="{
                          'text-yellow-600': icon.appearance === 'warning',
                          'text-blue-600': icon.appearance === 'info',
                          'text-red-600': icon.appearance === 'danger',
                          'text-green-600': icon.appearance === 'success',
                        }"
                        aria-hidden="true"
                      />
                    </div>
                    <div class="flex-1 text-center sm:text-left">
                      <DialogTitle as="header">
                        <slot name="body-title">
                          <h3
                            class="mb-2 text-lg font-medium leading-6 text-gray-900"
                          >
                            {{ options.title || 'Untitled' }}
                          </h3>
                        </slot>
                      </DialogTitle>

                      <slot name="body-content">
                        <p class="text-sm text-gray-600" v-if="options.message">
                          {{ options.message }}
                        </p>
                      </slot>
                    </div>
                  </div>
                </div>
              </slot>
              <div
                class="px-4 py-3 space-y-2 sm:space-x-reverse sm:space-x-3 sm:space-y-0 bg-gray-50 sm:px-6 sm:flex sm:flex-row-reverse"
                v-if="options?.actions || $slots.actions"
              >
                <slot name="actions" v-bind="{ close: () => (open = false) }">
                  <Button
                    class="w-full sm:w-max"
                    v-for="action in options.actions"
                    :key="action.label"
                    :loading="action.loading"
                    v-bind="action"
                    @click="handleAction(action)"
                  >
                    {{ action.label }}
                  </Button>
                </slot>
              </div>
            </slot>
          </div>
        </TransitionChild>
      </div>
    </HDialog>
  </TransitionRoot>
</template>

<script>
import { computed } from 'vue'
import {
  Dialog as HDialog,
  DialogOverlay,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import { Button, FeatherIcon } from 'frappe-ui'

export default {
  name: 'Dialog',
  props: {
    modelValue: {
      type: Boolean,
      required: true,
    },
    options: {
      type: Object,
      default() {
        return {}
      },
    },
  },
  emits: ['update:modelValue', 'close'],
  components: {
    HDialog,
    DialogOverlay,
    DialogTitle,
    TransitionChild,
    TransitionRoot,
    Button,
    FeatherIcon,
  },
  setup(props, { emit }) {
    let open = computed({
      get: () => props.modelValue,
      set: (val) => {
        emit('update:modelValue', val)
        if (!val) {
          emit('close')
        }
      },
    })
    return {
      open,
    }
  },
  methods: {
    handleAction(action) {
      let close = () => (this.open = false)
      if (action.handler && typeof action.handler === 'function') {
        action.loading = true
        let result = action.handler({ close })
        if (result && result.then) {
          result.then(() => (action.loading = false))
        } else {
          action.loading = false
        }
      } else {
        close()
      }
    },
  },
  computed: {
    icon() {
      if (!this.options?.icon) return null

      let icon = this.options.icon
      if (typeof icon === 'string') {
        icon = {
          name: icon,
          type: 'info',
        }
      }
      return icon
    },
  },
}
</script>
