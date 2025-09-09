<template>
  <div v-if="normalActions.length" class="flex gap-2">
    <Button
      v-for="action in normalActions"
      :key="action.label"
      :label="action.label"
      @click="action.onClick()"
    >
      <template v-if="action.icon" #prefix>
        <FeatherIcon :name="action.icon" class="h-4 w-4" />
      </template>
    </Button>
  </div>
  <div v-if="groupedWithLabelActions.length">
    <div v-for="g in groupedWithLabelActions" :key="g.label">
      <Dropdown v-slot="{ open }" :options="g.action">
        <Button :label="g.label">
          <template #suffix>
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4"
            />
          </template>
        </Button>
      </Dropdown>
    </div>
  </div>
  <Dropdown v-if="groupedActions.length" :options="groupedActions">
    <Button icon="more-horizontal" variant="ghost" />
  </Dropdown>
</template>

<script setup>
import { Dropdown } from "frappe-ui";
import { computed } from "vue";

const props = defineProps({
  actions: {
    type: Object,
    required: true,
  },
});

const normalActions = computed(() => {
  return props.actions.filter((action) => !action.group);
});

const groupedWithLabelActions = computed(() => {
  let _actions = [];

  props.actions
    .filter((action) => action.buttonLabel && action.group)
    .forEach((action) => {
      let groupIndex = _actions.findIndex(
        (a) => a.label === action.buttonLabel
      );
      if (groupIndex > -1) {
        _actions[groupIndex].action.push(action);
      } else {
        _actions.push({
          label: action.buttonLabel,
          action: [action],
        });
      }
    });
  return _actions;
});

const groupedActions = computed(() => {
  let _actions = [];
  _actions = _actions.concat(
    props.actions.filter((action) => action.group && !action.buttonLabel)
  );
  return _actions;
});
</script>
