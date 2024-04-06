<template>
  <Dialog
    v-model="show"
    :options="{
      title: 'Assign To',
      size: 'xl',
      actions: [
        {
          label: 'Cancel',
          variant: 'subtle',
          onClick: () => {
            show = false;
            _assignees = [];
          },
        },
        {
          label: 'Update',
          variant: 'solid',
          onClick: () => {
            emit('update', _assignees);
          },
        },
      ],
    }"
  >
    <template #body-content>
      <SearchComplete
        class="form-control"
        value=""
        doctype="User"
        @change="
          (option) => {
            addValue(option.value);
          }
        "
      >
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :name="option.value" size="sm" />
        </template>
        <template #item-label="{ option }">
          <Tooltip :text="option.value">
            {{ getUser(option.value).full_name }}
          </Tooltip>
        </template>
      </SearchComplete>
      <div class="mt-3 flex flex-wrap items-center gap-2">
        <Tooltip
          v-for="assignee in _assignees"
          :key="assignee.name"
          :text="assignee.name"
        >
          <Button
            :label="getUser(assignee.name).full_name"
            theme="gray"
            variant="outline"
          >
            <template #prefix>
              <UserAvatar :name="assignee.name" size="sm" />
            </template>
            <template #suffix>
              <FeatherIcon
                v-if="assignee.name !== owner"
                class="h-3.5"
                name="x"
                @click.stop="removeValue(assignee.name)"
              />
            </template>
          </Button>
        </Tooltip>
      </div>
      <ErrorMessage v-if="error" class="mt-2" :message="error" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, defineModel, watch } from "vue";
import { UserAvatar, SearchComplete } from "@/components";
import { useUserStore } from "@/stores/user";
let emit = defineEmits(["update"]);

const props = defineProps({
  assignees: {
    type: Array,
    default: () => [],
  },
});

const { getUser } = useUserStore();

const show = defineModel();
const _assignees = ref([]);

watch(
  () => props.assignees,
  (newValue) => {
    _assignees.value = JSON.parse(JSON.stringify(newValue));
  }
);

const error = ref("");

const addValue = (value) => {
  error.value = "";
  let obj = {
    name: value,
    image: getUser(value).user_image,
    label: getUser(value).full_name,
  };
  if (!_assignees.value.find((assignee) => assignee.name === value)) {
    _assignees.value.push(obj);
  }
};

const removeValue = (value) => {
  _assignees.value = _assignees.value.filter(
    (assignee) => assignee.name !== value
  );
};
</script>
