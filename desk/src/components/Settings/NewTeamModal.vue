<template>
  <Dialog
    v-model="show"
    :options="{
      title: 'New team',
      actions: [
        {
          label: 'Create',
          variant: 'solid',
          onClick: () => {
            newTeam.submit();
          },
        },
      ],
    }"
  >
    <template #body-content>
      <form class="space-y-2" @submit.prevent="newTeam.submit">
        <FormControl
          v-model="newTeamTitle"
          label="Title"
          placeholder="Product experts"
          type="text"
        />
      </form>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { createResource, toast } from "frappe-ui";
import { isEmpty } from "lodash";
import { ref } from "vue";

const emit = defineEmits(["create"]);
const show = defineModel();

const newTeamTitle = ref(null);
const newTeam = createResource({
  url: "frappe.client.insert",
  makeParams() {
    return {
      doc: {
        doctype: "HD Team",
        team_name: newTeamTitle.value,
      },
    };
  },
  validate(params) {
    if (isEmpty(params.doc.team_name)) return "Title is required";
  },
  auto: false,
  onSuccess() {
    toast.success("Team created");
    newTeamTitle.value = null;
    show.value = false;
    emit("create");
  },
});
</script>

<style scoped></style>
