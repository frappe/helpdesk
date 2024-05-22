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
            newAssignees = [];
            assigneesToRemove = [];
            currentAssignees = JSON.parse(JSON.stringify(props.assignees));
          },
        },
        {
          label: 'Update',
          variant: 'solid',
          onClick: () => {
            updateAssignees();
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
        :reset-input="true"
        @change="
          (option) => {
            addAssignee(option.value);
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
          v-for="currentAssignee in currentAssignees"
          :key="currentAssignee.name"
          :text="currentAssignee.name"
        >
          <Button
            :label="getUser(currentAssignee.name).full_name"
            theme="gray"
            variant="outline"
          >
            <template #prefix>
              <UserAvatar :name="currentAssignee.name" size="sm" />
            </template>
            <template #suffix>
              <FeatherIcon
                class="h-3.5"
                name="x"
                @click.stop="removeCurrentAssignee(currentAssignee.name)"
              />
            </template>
          </Button>
        </Tooltip>
        <Tooltip
          v-for="newAssignee in newAssignees"
          :key="newAssignee.name"
          :text="newAssignee.name"
        >
          <Button
            :label="getUser(newAssignee.name).full_name"
            theme="gray"
            variant="outline"
          >
            <template #prefix>
              <UserAvatar :name="newAssignee.name" size="sm" />
            </template>
            <template #suffix>
              <FeatherIcon
                class="h-3.5"
                name="x"
                @click.stop="removeAssignee(newAssignee.name)"
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
import { call } from "frappe-ui";
import { UserAvatar, SearchComplete } from "@/components";
import { useUserStore } from "@/stores/user";

const props = defineProps({
  assignees: {
    type: Array,
    default: () => [],
  },
  doctype: {
    type: String,
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["update"]);

const { getUser } = useUserStore();

const show = defineModel();
const newAssignees = ref([]);
const currentAssignees = ref([...props.assignees]);
const assigneesToRemove = [];

const error = ref("");

const addAssignee = (value) => {
  error.value = "";
  const assigneeExists = [
    ...newAssignees.value,
    ...currentAssignees.value,
  ].find((assignee) => assignee.name === value);

  if (!assigneeExists) {
    let obj = {
      name: value,
      image: getUser(value).user_image,
      label: getUser(value).full_name,
    };
    newAssignees.value.push(obj);
  }
};

const removeAssignee = (value) => {
  newAssignees.value = newAssignees.value.filter(
    (assignee) => assignee.name !== value
  );
};

const removeCurrentAssignee = (value) => {
  currentAssignees.value = currentAssignees.value.filter(
    (assignee) => assignee.name !== value
  );
  assigneesToRemove.push(value);
};

function updateAssignees() {
  const promises = [];
  for (const assigneeToRemove of assigneesToRemove) {
    promises.push(
      call("frappe.desk.form.assign_to.remove", {
        doctype: props.doctype,
        name: props.docname,
        assign_to: assigneeToRemove,
      })
    );
  }

  if (newAssignees.value.length) {
    promises.push(
      call("frappe.desk.form.assign_to.add", {
        doctype: props.doctype,
        name: props.docname,
        assign_to: newAssignees.value.map((assignee) => assignee.name),
      })
    );
  }

  Promise.all(promises)
    .then(() => {
      emit("update");
      show.value = false;
    })
    .catch((e) => {
      error.value = e.message;
    });
}
</script>
