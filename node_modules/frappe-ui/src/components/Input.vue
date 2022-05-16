<template>
  <label :class="[type == 'checkbox' ? 'flex' : 'block', $attrs.class]">
    <span
      v-if="label && type != 'checkbox'"
      class="block mb-2 text-sm leading-4 text-gray-700"
    >
      {{ label }}
    </span>
    <input
      v-if="
        ['text', 'number', 'checkbox', 'email', 'password', 'date'].includes(
          type
        )
      "
      v-bind="inputAttributes"
      class="placeholder-gray-500"
      ref="input"
      :class="[
        {
          'block w-full form-input': type != 'checkbox',
          'form-checkbox': type == 'checkbox',
        },
        inputClass,
      ]"
      :type="type || 'text'"
      :disabled="disabled"
      :placeholder="placeholder"
      :value="passedInputValue"
    />
    <textarea
      v-if="type === 'textarea'"
      v-bind="inputAttributes"
      :class="['block w-full resize-none form-textarea', inputClass]"
      ref="input"
      :value="passedInputValue"
      :disabled="disabled"
      :rows="rows || 3"
      @blur="$emit('blur', $event)"
    ></textarea>
    <select
      v-bind="inputAttributes"
      class="block w-full form-select"
      ref="input"
      v-if="type === 'select'"
      :disabled="disabled"
    >
      <option
        v-for="option in selectOptions"
        :key="option.value"
        :value="option.value"
        :selected="passedInputValue === option.value"
      >
        {{ option.label }}
      </option>
    </select>
    <span
      v-if="label && type == 'checkbox'"
      class="inline-block ml-2 text-base leading-4"
    >
      {{ label }}
    </span>
  </label>
</template>

<script>
import { debounce } from 'frappe-ui'

export default {
  name: 'Input',
  inheritAttrs: false,
  expose: ['getInputValue'],
  props: {
    label: {
      type: String,
    },
    type: {
      type: String,
      validator(value) {
        let isValid = [
          'text',
          'number',
          'checkbox',
          'textarea',
          'select',
          'email',
          'password',
          'date',
        ].includes(value)
        if (!isValid) {
          console.warn(`Invalid value "${value}" for "type" prop for Input`)
        }
        return isValid
      },
    },
    modelValue: {
      type: [String, Number, Boolean, Object, Array],
    },
    inputClass: {
      type: [String, Array, Object],
    },
    debounce: {
      type: Number,
    },
    options: {
      type: Array,
    },
    disabled: {
      type: Boolean,
    },
    rows: {
      type: Number,
    },
    placeholder: {
      type: String,
    },
  },
  emits: ['blur', 'input', 'change', 'update:modelValue'],
  methods: {
    focus() {
      this.$refs.input.focus()
    },
    blur() {
      this.$refs.input.blur()
    },
    getInputValue(e) {
      let $input = e ? e.target : this.$refs.input
      let value = $input.value
      if (this.type == 'checkbox') {
        value = $input.checked
      }
      return value
    },
  },
  computed: {
    passedInputValue() {
      if ('value' in this.$attrs) {
        return this.$attrs.value
      }
      return this.modelValue || null
    },
    inputAttributes() {
      let onInput = (e) => {
        this.$emit('input', this.getInputValue(e))
      }
      if (this.debounce) {
        onInput = debounce(onInput, this.debounce)
      }
      return Object.assign({}, this.$attrs, {
        onInput,
        onChange: (e) => {
          this.$emit('change', this.getInputValue(e))
          this.$emit('update:modelValue', this.getInputValue(e))
        },
      })
    },
    selectOptions() {
      return this.options.map((option) => {
        if (typeof option === 'string') {
          return {
            label: option,
            value: option,
          }
        }
        return option
      })
    },
  },
}
</script>
