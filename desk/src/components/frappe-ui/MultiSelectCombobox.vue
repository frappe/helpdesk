<template>
  <Combobox
    v-model="selectedValue"
    :multiple="multiple"
    nullable
    v-slot="{ open: isComboboxOpen }"
  >
    <Popover class="w-full" v-model:show="showOptions" :placement="placement">
      <template
        #target="{ open: openPopover, togglePopover, close: closePopover }"
      >
        <slot
          name="target"
          v-bind="{
            open: openPopover,
            close: closePopover,
            togglePopover,
            isOpen: isComboboxOpen,
          }"
        >
          <div class="w-full space-y-1.5">
            <label v-if="$props.label" class="block text-xs text-gray-600">
              {{ $props.label }}
            </label>
            <button
              class="flex h-7 w-full items-center justify-between gap-2 rounded bg-gray-100 py-1 px-2 transition-colors hover:bg-gray-200 focus:ring-2 focus:ring-gray-400"
              :class="[
                isComboboxOpen ? 'bg-gray-200' : '',
                $props.buttonClasses,
                disabled ? 'cursor-not-allowed opacity-50' : '',
              ]"
              @click="
                () => {
                  !disabled && togglePopover();
                }
              "
            >
              <div class="flex flex-1 items-center gap-2 overflow-hidden">
                <slot name="prefix" />
                <span
                  v-if="selectedValue"
                  class="flex-1 truncate text-left text-base leading-5"
                >
                  {{ displayValue(selectedValue) }}
                </span>
                <span v-else class="text-base leading-5 text-gray-600">
                  {{ placeholder || "" }}
                </span>
                <slot name="suffix" />
              </div>
              <FeatherIcon
                v-show="!loading"
                name="chevron-down"
                class="h-4 w-4 text-gray-600"
                aria-hidden="true"
              />
              <LoadingIndicator
                class="h-4 w-4 text-gray-600"
                v-show="loading"
              />
            </button>
          </div>
        </slot>
      </template>
      <template #body="{ isOpen, togglePopover }">
        <div v-show="isOpen">
          <div
            class="relative mt-1 overflow-hidden rounded-lg bg-white text-base shadow-2xl"
            :class="bodyClasses"
          >
            <ComboboxOptions
              class="flex max-h-[15rem] flex-col overflow-hidden p-1.5"
              static
            >
              <div
                v-if="!hideSearch"
                class="relative mb-1 w-full flex-shrink-0"
              >
                <ComboboxInput
                  ref="searchInput"
                  class="form-input w-full"
                  type="text"
                  :value="query"
                  @change="query = $event.target.value"
                  autocomplete="off"
                  placeholder="Search"
                />
                <button
                  class="absolute right-0 inline-flex h-7 w-7 items-center justify-center"
                  @click="selectedValue = null"
                >
                  <FeatherIcon name="x" class="w-4" />
                </button>
              </div>
              <div class="w-full flex-1 overflow-y-auto">
                <div
                  v-for="group in groups"
                  :key="group.key"
                  v-show="group.items.length > 0"
                >
                  <div
                    v-if="group.group && !group.hideLabel"
                    class="sticky top-0 truncate bg-white px-2.5 py-1.5 text-sm font-medium text-gray-600"
                  >
                    {{ group.group }}
                  </div>
                  <ComboboxOption
                    as="template"
                    v-for="(option, idx) in group.items.slice(0, 50)"
                    :key="option?.value || idx"
                    :value="option"
                    v-slot="{ active, selected }"
                  >
                    <li
                      :class="[
                        'flex h-7 cursor-pointer items-center justify-between rounded px-2.5 text-base',
                        { 'bg-gray-100': active },
                      ]"
                    >
                      <div
                        class="flex flex-1 items-center gap-2 overflow-hidden"
                      >
                        <div
                          v-if="$slots['item-prefix'] || $props.multiple"
                          class="flex-shrink-0"
                        >
                          <slot
                            name="item-prefix"
                            v-bind="{ active, selected, option }"
                          >
                            <LucideSquare
                              v-show="!isOptionSelected(option)"
                              class="h-4 w-4 text-gray-700"
                            />
                            <LucideCheckSquare
                              v-show="isOptionSelected(option)"
                              class="h-4 w-4 text-gray-700"
                            />
                          </slot>
                        </div>
                        <span class="flex-1 truncate">
                          {{ getLabel(option) }}
                        </span>
                      </div>

                      <div
                        v-if="$slots['item-suffix'] || option?.description"
                        class="ml-2 flex-shrink-0"
                      >
                        <slot
                          name="item-suffix"
                          v-bind="{ active, selected, option }"
                        >
                          <div
                            v-if="option?.description"
                            class="text-sm text-gray-600"
                          >
                            {{ option.description }}
                          </div>
                        </slot>
                      </div>
                    </li>
                  </ComboboxOption>
                </div>
              </div>
              <li
                v-if="groups.length == 0"
                class="rounded-md px-2.5 py-1.5 text-base text-gray-600"
              >
                No results found
              </li>
            </ComboboxOptions>

            <div
              v-if="$slots.footer || showFooter || multiple"
              class="border-t p-1"
            >
              <slot name="footer" v-bind="{ togglePopover }">
                <div
                  v-if="multiple"
                  class="flex items-center justify-end gap-1"
                >
                  <Button
                    v-if="!areAllOptionsSelected"
                    label="Select All"
                    @click.stop="selectAll"
                  />
                </div>
                <div v-else class="flex items-center justify-end">
                  <Button label="Clear" @click.stop="selectedValue = null" />
                </div>
              </slot>
            </div>
          </div>
        </div>
      </template>
    </Popover>
  </Combobox>
</template>

<script>
import {
  Combobox,
  ComboboxButton,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from "@headlessui/vue";
import { LoadingIndicator, Popover } from "frappe-ui";
import { nextTick } from "vue";
import LucideCheckSquare from "~icons/lucide/check-square";
import LucideSquare from "~icons/lucide/square";

export default {
  name: "Autocomplete",
  props: [
    "label",
    "modelValue",
    "options",
    "placeholder",
    "bodyClasses",
    "multiple",
    "loading",
    "hideSearch",
    "autoFocus",
    "placement",
    "showFooter",
    "buttonClasses",
    "disabled",
  ],
  emits: ["update:modelValue", "update:query", "change"],
  components: {
    Popover,
    Combobox,
    ComboboxInput,
    ComboboxOptions,
    ComboboxOption,
    ComboboxButton,
    LucideCheckSquare,
    LucideSquare,
  },
  expose: ["togglePopover"],
  data() {
    return {
      query: "",
      showOptions: false,
    };
  },
  computed: {
    selectedValue: {
      get() {
        let _selectedOptions;
        if (!this.multiple) {
          _selectedOptions = this.findOption(this.modelValue);
          if (this.modelValue && !_selectedOptions) {
            _selectedOptions = this.sanitizeOption(this.modelValue);
          }
          return _selectedOptions;
        }

        _selectedOptions = this.modelValue?.map((v) => {
          const option = this.findOption(v);
          if (option) return option;
          return this.sanitizeOption(v);
        });
        if (this.modelValue && !_selectedOptions.length) {
          _selectedOptions = this.sanitizeOptions(this.modelValue);
        }
        return _selectedOptions;
      },
      set(val) {
        this.query = "";
        if (val && !this.multiple) this.showOptions = false;
        this.$emit("update:modelValue", val);
      },
    },
    groups() {
      if (!this.options || this.options.length == 0) return [];

      let groups = this.options[0]?.group
        ? this.options
        : [{ group: "", items: this.sanitizeOptions(this.options) }];

      return groups
        .map((group, i) => {
          return {
            key: i,
            group: group.group,
            hideLabel: group.hideLabel || false,
            items: this.filterOptions(this.sanitizeOptions(group.items)),
          };
        })
        .filter((group) => group.items.length > 0);
    },
    allOptions() {
      return this.groups.flatMap((group) => group.items);
    },
    areAllOptionsSelected() {
      if (!this.multiple) return false;
      return this.allOptions.length === this.selectedValue?.length;
    },
  },
  watch: {
    query(q) {
      this.$emit("update:query", q);
    },
    showOptions(val) {
      if (val) nextTick(() => this.$refs.searchInput?.$el?.focus());
    },
  },
  methods: {
    togglePopover(val) {
      this.showOptions = val ?? !this.showOptions;
    },
    findOption(option) {
      if (!option) return option;
      return this.allOptions.find((o) => o.value === (option.value || option));
    },
    filterOptions(options) {
      if (!this.query) return options;
      return fuzzySearch(options, {
        term: this.query,
        keys: ["label", "value"],
      });
    },
    displayValue(option) {
      if (!option) return "";

      if (!this.multiple) {
        if (typeof option === "object") {
          return this.getLabel(option);
        }
        let selectedOption = this.allOptions.find((o) => o.value === option);
        return this.getLabel(selectedOption);
      }

      if (!Array.isArray(option)) return "";

      if (option.length === 0) return "";
      if (option.length === 1) return this.getLabel(option[0]);
      return `${option.length} values`;
      // in case of `multiple`, option is an array of values
      // so the display value should be comma separated labels
      // return option
      // 	.map((v) => {
      // 		if (typeof v === 'object') {
      // 			return this.getLabel(v)
      // 		}
      // 		let selectedOption = this.allOptions.find((o) => o.value === v)
      // 		return this.getLabel(selectedOption)
      // 	})
      // 	.join(', ')
    },
    getLabel(option) {
      if (typeof option !== "object") return option;
      return option?.label || option?.value || "No label";
    },
    sanitizeOptions(options) {
      if (!options) return [];
      // in case the options are just strings, convert them to objects
      return options.map((option) => this.sanitizeOption(option));
    },
    sanitizeOption(option) {
      return typeof option === "string"
        ? { label: option, value: option }
        : option;
    },
    isOptionSelected(option) {
      if (!this.multiple) {
        return this.selectedValue?.value === option.value;
      }
      return this.selectedValue?.find((v) => v && v.value === option.value);
    },
    selectAll() {
      this.selectedValue = this.allOptions;
    },
    fuzzySearch(arr, { term, keys }) {
      // search for term in all keys of arr items and sort by relevance
      const lowerCaseTerm = term.toLowerCase();
      const results = arr.reduce((acc, item) => {
        const score = keys.reduce((acc, key) => {
          const value = item[key];
          if (value) {
            const match = value.toLowerCase().indexOf(lowerCaseTerm);
            if (match !== -1) {
              return acc + match + 1;
            }
          }
          return acc;
        }, 0);
        if (score) {
          acc.push({ item, score });
        }
        return acc;
      }, []);
      return results.sort((a, b) => a.score - b.score).map((item) => item.item);
    },
  },
};
</script>
