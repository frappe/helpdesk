<template>
  <NestedPopover>
    <template #target>
      <Button label="Filters" theme="gray" variant="outline">
        <template #prefix>
          <LucideListFilter class="h-4 w-4" />
        </template>
        <template v-if="resource.filters" #suffix>
          <Badge
            :label="Object.keys(resource.filters).length"
            theme="gray"
            variant="subtle"
          />
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div class="my-2 rounded-lg bg-white shadow-lg">
        <div class="min-w-[300px] space-y-2 p-2">
          <div
            v-for="(v, f) in resource.filters"
            :key="f"
            :set="
              (m = metaState[doctype]?.fields.find((_f) => _f.fieldname === f))
            "
          >
            <div v-if="m" class="flex items-center gap-2">
              <div class="!w-[140px]">
                <FormControl
                  type="select"
                  :value="m.label"
                  :model-value="m.label"
                  :options="fields"
                  placeholder="Filter by..."
                />
              </div>
              <div class="text-base">is</div>
              <div class="!w-[140px]">
                <SearchComplete
                  v-if="typeLink.includes(m.fieldtype)"
                  placeholder="Value"
                  :doctype="m.options"
                  :value="v"
                  @change="(val) => (resource.filters[f] = val.value)"
                />
                <component
                  :is="getValSelect(m.fieldtype, m.options)"
                  v-else
                  placeholder="Value"
                  :model-value="v"
                  @update:model-value="(val) => (resource.filters[f] = val)"
                />
              </div>
              <Button
                variant="subtle"
                @click="() => delete resource.filters[f]"
              >
                <template #icon>
                  <LucideX class="h-4 w-4" />
                </template>
              </Button>
            </div>
          </div>
          <div class="flex items-center justify-end gap-2">
            <Button variant="subtle" @click="() => resource.fetch()">
              <template #icon>
                <LucideCheck class="h-4 w-4" />
              </template>
            </Button>
            <Autocomplete
              value=""
              :options="[]"
              placeholder="Filter by..."
              @change="(e) => setfilter(e)"
            >
              <template #target="{ togglePopover }">
                <Button variant="subtle" @click="() => togglePopover()">
                  <template #icon>
                    <LucidePlus class="h-4 w-4" />
                  </template>
                </Button>
              </template>
            </Autocomplete>
            <Button
              variant="subtle"
              @click="
                () => {
                  resource.filters = undefined;
                  resource.fetch();
                }
              "
            >
              <template #icon>
                <LucideX class="h-4 w-4" />
              </template>
            </Button>
            <!-- <Button -->
            <!--   v-if="storage.size" -->
            <!--   class="!text-gray-600" -->
            <!--   variant="ghost" -->
            <!--   label="Clear all filter" -->
            <!--   @click="() => clearfilter(close)" -->
            <!-- /> -->
          </div>
        </div>
      </div>
    </template>
  </NestedPopover>
</template>
<script setup lang="ts">
import { computed, h, watch } from 'vue';
import { Autocomplete, Badge, Dropdown, FormControl } from 'frappe-ui';
import { useDebounceFn } from '@vueuse/core';
import { useFilter } from '@/composables/filter';
import { NestedPopover, SearchComplete } from '@/components';
import { metaState } from '@/resources';

// const props = defineProps({
//   doctype: {
//     type: String,
//     required: true,
//   },
//   resource: {}
// });

const props = defineProps<{
  doctype: string;
  resource: any;
}>();

// const { apply, fields, storage } = useFilter(props.doctype);
const typeCheck = ['Check'];
const typeLink = ['Link'];
const typeNumber = ['Float', 'Int'];
const typeSelect = ['Select'];
const typeString = ['Data', 'Long Text', 'Small Text', 'Text Editor', 'Text'];
const fields = computed(() =>
  metaState[props.doctype]?.fields
    .filter((f) => ['Link', 'Select'].includes(f.fieldtype))
    .map((f) => ({
      label: f.label,
      value: f.fieldname,
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
);

// watch(
//   storage,
//   useDebounceFn(() => apply(), 300),
//   { deep: true }
// );

function getOperators(fieldtype) {
  let options = [];
  if (typeString.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: 'equals' },
        { label: 'Not Equals', value: 'not equals' },
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not like' },
      ]
    );
  }
  if (typeNumber.includes(fieldtype)) {
    options.push(
      ...[
        { label: '<', value: '<' },
        { label: '>', value: '>' },
        { label: '<=', value: '<=' },
        { label: '>=', value: '>=' },
        { label: 'Equals', value: 'equals' },
        { label: 'Not Equals', value: 'not equals' },
      ]
    );
  }
  if (typeSelect.includes(fieldtype) || typeLink.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Is', value: 'is' },
        { label: 'Is Not', value: 'is not' },
      ]
    );
  }
  if (typeCheck.includes(fieldtype)) {
    options.push(...[{ label: 'Equals', value: 'equals' }]);
  }
  return options;
}

function getValSelect(fieldtype, options) {
  if (typeSelect.includes(fieldtype) || typeCheck.includes(fieldtype)) {
    const _options =
      fieldtype == 'Check' ? ['Yes', 'No'] : getSelectOptions(options);
    return h(FormControl, {
      type: 'select',
      options: _options.map((o) => ({
        label: o,
        value: o,
      })),
    });
  } else {
    return h(FormControl, { type: 'text' });
  }
}

function getDefaultValue(field) {
  if (typeSelect.includes(field.fieldtype)) {
    return getSelectOptions(field.options)[0];
  }
  if (typeCheck.includes(field.fieldtype)) {
    return 'Yes';
  }
  return '';
}

function getDefaultOperator(fieldtype) {
  if (typeSelect.includes(fieldtype) || typeLink.includes(fieldtype)) {
    return 'is';
  }
  if (typeCheck.includes(fieldtype) || typeNumber.includes(fieldtype)) {
    return 'equals';
  }
  return 'like';
}

function getSelectOptions(options) {
  return options.split('\n');
}

// function setfilter(data) {
//   storage.value.add({
//     field: {
//       label: data.label,
//       fieldname: data.value,
//       fieldtype: data.fieldtype,
//       options: data.options,
//     },
//     fieldname: data.value,
//     operator: getDefaultOperator(data.fieldtype),
//     value: getDefaultValue(data),
//   });
// }
//
// function updateFilter(data, index) {
//   storage.value.delete(Array.from(storage.value)[index]);
//   storage.value.add({
//     fieldname: data.value,
//     operator: getDefaultOperator(data.fieldtype),
//     value: getDefaultValue(data),
//     field: {
//       label: data.label,
//       fieldname: data.value,
//       fieldtype: data.fieldtype,
//       options: data.options,
//     },
//   });
// }
//
// function removeFilter(index) {
//   storage.value.delete(Array.from(storage.value)[index]);
// }
//
// function clearfilter(close) {
//   storage.value.clear();
//   close();
// }
</script>
