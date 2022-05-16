<template>
  <Menu as="div" class="relative inline-block text-left" v-slot="{ open }">
    <MenuButton as="div">
      <slot v-if="$slots.default" v-bind="{ open }"></slot>
      <Button v-else v-bind="button" :active="open">
        {{ button ? button?.label || null : 'Options' }}
      </Button>
    </MenuButton>

    <transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <MenuItems
        class="absolute z-10 mt-2 bg-white divide-y divide-gray-100 rounded-md shadow-lg min-w-40 ring-1 ring-black ring-opacity-5 focus:outline-none"
        :class="
          placement === 'left'
            ? 'left-0 origin-top-left'
            : 'right-0 origin-top-right'
        "
      >
        <div v-for="group in groups" :key="group.key" class="px-1 py-1">
          <div
            v-if="group.group && !group.hideLabel"
            class="px-2 py-1 text-xs font-semibold tracking-wider text-gray-500 uppercase"
          >
            {{ group.group }}
          </div>
          <MenuItem
            v-for="item in group.items"
            :key="item.label"
            v-slot="{ active }"
          >
            <button
              :class="[
                active ? 'bg-gray-100' : 'text-gray-900',
                'group flex rounded-md items-center w-full px-2 py-2 text-sm',
              ]"
              @click="item.onClick"
            >
              <FeatherIcon
                v-if="item.icon"
                :name="item.icon"
                class="flex-shrink-0 w-4 h-4 mr-2 text-gray-500"
                aria-hidden="true"
              />
              <span class="whitespace-nowrap">
                {{ item.label }}
              </span>
            </button>
          </MenuItem>
        </div>
      </MenuItems>
    </transition>
  </Menu>
</template>

<script>
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue'
import { FeatherIcon } from 'frappe-ui'

export default {
  name: 'NewDropdown',
  props: ['button', 'options', 'placement'],
  components: {
    Menu,
    MenuButton,
    MenuItems,
    MenuItem,
    FeatherIcon,
  },
  methods: {
    normalizeDropdownItem(option) {
      let onClick = option.handler || null
      if (!onClick && option.route && this.$router) {
        onClick = () => this.$router.push(option.route)
      }
      return {
        label: option.label,
        icon: option.icon,
        group: option.group,
        onClick,
      }
    },
    filterOptions(options) {
      return (options || [])
        .filter(Boolean)
        .filter((option) => (option.condition ? option.condition() : true))
        .map((option) => this.normalizeDropdownItem(option))
    },
  },
  computed: {
    groups() {
      let groups = this.options[0]?.group
        ? this.options
        : [{ group: '', items: this.options }]

      return groups.map((group, i) => {
        return {
          key: i,
          group: group.group,
          hideLabel: group.hideLabel || false,
          items: this.filterOptions(group.items),
        }
      })
    },
  },
}
</script>
