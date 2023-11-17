<template>
  <div
    class="group mx-5 flex h-10 items-center gap-2 whitespace-nowrap px-2.5 text-base"
    :class="{
      'bg-blue-100': selection.storage.has(data.name),
      'hover:bg-blue-200': selection.storage.has(data.name),
      'hover:bg-gray-100': !selection.storage.has(data.name),
      'cursor-pointer': !!data.onClick,
      ...data.class,
    }"
  >
    <FormControl
      v-if="checkbox"
      type="checkbox"
      :model-value="selection.storage.has(data.name)"
      @update:model-value="selection.toggle(data.name)"
    />
    <component
      :is="isFunction(data.onClick) ? 'span' : RouterLink"
      as="template"
      :to="data.onClick"
      class="flex w-full items-center gap-2"
      @click="
        (event) => {
          if (isFunction(data.onClick)) {
            event.preventDefault();
            data.onClick();
          }
        }
      "
    >
      <div
        v-for="c in metaState[doctype]?.fields.filter((f) => f.in_list_view)"
        :key="c.fieldname"
        :class="{
          [c.text]: data[c.fieldname],
          'text-gray-300': !data[c.fieldname],
        }"
      >
        <div v-if="!hiddenColumns.has(c.fieldname)" :class="[c.width]">
          <div
            class="w-max max-w-full truncate"
            :class="[c.align]"
            @click="(event) => filterFunc(event, c)"
          >
            <slot :name="c.fieldname" :data="data">
              <span v-if="c.type === 'timeAgo' && data[c.fieldname]">
                <Tooltip :text="dayjs(data[c.fieldname]).long()">
                  {{ dayjs(data[c.fieldname]).fromNow() }}
                </Tooltip>
              </span>
              <span v-else>{{ data[c.fieldname] || '⸺' }}</span>
            </slot>
          </div>
        </div>
      </div>
    </component>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue';
import { RouterLink } from 'vue-router';
import { FormControl, Tooltip } from 'frappe-ui';
import { isFunction } from 'lodash';
import { Column } from '@/types';
import { getAssign } from '@/utils';
import { dayjs } from '@/dayjs';
import { useFieldsStore } from '@/stores/fields';
import { useColumns } from '@/composables/columns';
import { useFilter } from '@/composables/filter';
import { metaState } from '@/resources';
import { selection } from './selection';
import { CheckboxKey, DocTypeKey } from './symbols';

interface I {
  name: string;
  class?: Record<string, string>;
  onClick?: () => void;
  [key: string]: unknown;
}

interface P {
  data: I;
}

const checkbox = inject(CheckboxKey);
const doctype = inject(DocTypeKey);
const props = defineProps<P>();
const { storage: hiddenColumns } = useColumns(doctype);
const fieldsStore = useFieldsStore();
const filter = useFilter(doctype);

async function filterFunc(event: InputEvent, c: Column) {
  if (!doctype) return;
  await fieldsStore.fetch(doctype);
  fieldsStore
    .get(doctype)
    .filter((field) => ['Link', 'Select'].includes(field.fieldtype))
    .filter((field) => field.fieldname === c.key)
    .map((field) => {
      let val = props.data[c.key] as string;
      if (field.fieldname === '_assign') {
        val = getAssign(val);
      }
      return {
        fieldname: field.fieldname,
        label: field.label,
        operator: 'is',
        value: val,
      };
    })
    .filter((field) => field.value)
    .forEach((field) => {
      event.preventDefault();
      event.stopPropagation();
      filter.add(field);
      filter.apply();
    });
}
</script>
