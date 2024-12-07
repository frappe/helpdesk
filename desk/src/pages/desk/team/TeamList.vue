<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Teams</div>
      </template>
      <template #right-header>
        <Button
          label="New team"
          theme="gray"
          variant="solid"
          @click="showNewDialog = !showNewDialog"
          iconLeft="plus"
        />
      </template>
    </LayoutHeader>
    <ListViewBuilder
      :options="{
        doctype: 'HD Team',
      }"
    />
    <Dialog
      v-model="showNewDialog"
      :options="{
        title: 'New team',
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
          <Button
            :disabled="isEmpty(newTeamTitle)"
            class="w-full"
            label="Create"
            theme="gray"
            variant="solid"
          />
        </form>
      </template>
    </Dialog>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { createResource, usePageMeta, Dialog, FormControl } from "frappe-ui";
import { isEmpty } from "lodash";
import { AGENT_PORTAL_TEAM_SINGLE } from "@/router";
import { createListManager } from "@/composables/listManager";
import { useError } from "@/composables/error";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";

const router = useRouter();
const showNewDialog = ref(false);
const newTeamTitle = ref(null);
const emptyMessage = "No Teams Found";

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
    router.replace({
      name: AGENT_PORTAL_TEAM_SINGLE,
      params: {
        teamId: newTeamTitle.value,
      },
    });
  },
  onError: useError({ title: "Error creating team" }),
});

usePageMeta(() => {
  return {
    title: "Teams",
  };
});
</script>
