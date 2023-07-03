<template>
  <span>
    <div class="flex flex-col">
      <TopBar :title="teamId" :back-to="AGENT_PORTAL_TEAM_LIST">
        <template #right>
          <Dropdown :options="docOptions">
            <Button icon="more-horizontal" variant="ghost" />
          </Dropdown>
        </template>
      </TopBar>
      <div class="m-6">
        <div class="container">
          <div class="space-y-4">
            <div class="space-y-2">
              <Input label="Ignore restrictions" type="checkbox" />
              <div class="text-sm text-gray-700">
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
                eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut
                enim ad minim veniam, quis nostrud exercitation ullamco laboris
                nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor
                in reprehenderit in voluptate velit esse cillum dolore eu fugiat
                nulla pariatur
              </div>
            </div>
            <MultiSelect v-model:items="agents" />
          </div>
        </div>
      </div>
    </div>
    <Dialog v-model="showRename" :options="renameDialogOptions">
      <template #body-content>
        <div class="space-y-2">
          <FormControl
            v-model="title"
            label="Title"
            placeholder="Product Experts"
          />
          <Button
            label="Confirm"
            theme="gray"
            variant="subtle"
            class="w-full"
            :disabled="title === teamId"
            @click="renameTeam"
          />
        </div>
      </template>
    </Dialog>
    <Dialog v-model="showDelete" :options="deleteDialogOptions" />
  </span>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import {
  createResource,
  Button,
  Dialog,
  Dropdown,
  FormControl,
  createDocumentResource,
} from "frappe-ui";
import { AGENT_PORTAL_TEAM_LIST, AGENT_PORTAL_TEAM_SINGLE } from "@/router";
import { createToast } from "@/utils/toasts";
import MultiSelect from "@/components/MultiSelect.vue";
import TopBar from "@/components/TopBar.vue";

const props = defineProps({
  teamId: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const agents = ref([]);
const showRename = ref(false);
const showDelete = ref(false);
const team = createDocumentResource({
  doctype: "HD Team",
  name: props.teamId,
  auto: true,
  delete: {
    onSuccess() {
      router.replace({
        name: AGENT_PORTAL_TEAM_LIST,
      });
    },
    onError(error) {
      const msg = error.messages.join(", ");
      createToast({
        title: "Error deleting team",
        text: msg,
        icon: "x",
        iconClasses: "text-red-500",
      });
    },
  },
});
const title = computed({
  get() {
    return team.doc?.name;
  },
  set(t: string) {
    team.doc.name = t;
  },
});
const docOptions = [
  {
    label: "Rename",
    icon: "edit-3",
    onClick: () => (showRename.value = !showRename.value),
  },
  {
    label: "Delete",
    icon: "trash-2",
    onClick: () => (showDelete.value = !showDelete.value),
  },
];
const renameDialogOptions = { title: "Rename team" };
const deleteDialogOptions = {
  title: "Delete team",
  message: `Are you sure you want to delete ${props.teamId}? This action cannot be reversed!`,
  actions: [
    {
      label: "Confirm",
      theme: "red",
      variant: "subtle",
      onClick: () => team.delete.submit(),
    },
  ],
};

function renameTeam() {
  const r = createResource({
    url: "frappe.client.rename_doc",
    makeParams() {
      return {
        doctype: "HD Team",
        old_name: props.teamId,
        new_name: title.value,
      };
    },
    validate(params) {
      if (!params.new_name) return "New title is required";
      if (params.new_name === params.old_name)
        return "New and old title cannot be same";
    },
    onSuccess() {
      router.replace({
        name: AGENT_PORTAL_TEAM_SINGLE,
        params: {
          teamId: title.value,
        },
      });
    },
    onError(error) {
      const msg = error.message ? error.message : error.messages.join(", ");
      createToast({
        title: "Error renaming team",
        text: msg,
        icon: "x",
        iconClasses: "text-red-500",
      });
    },
  });

  r.submit();
}
</script>
