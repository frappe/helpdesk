<template>
  <span>
    <div class="flex flex-col">
      <PageTitle class="border-b">
        <template #title>
          <BreadCrumbs
            :items="[
              {
                label: 'Teams',
                route: {
                  name: AGENT_PORTAL_TEAM_LIST,
                },
              },
              {
                label: teamId,
              },
            ]"
          />
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <Button
              label="Add member"
              theme="gray"
              variant="solid"
              @click="showAddMember = !showAddMember"
            >
              <template #prefix>
                <IconPlus class="h-4 w-4" />
              </template>
            </Button>
            <Dropdown :options="docOptions">
              <Button variant="ghost">
                <template #icon>
                  <IconMoreHorizontal class="h-4 w-4" />
                </template>
              </Button>
            </Dropdown>
          </div>
        </template>
      </PageTitle>
      <div class="my-6">
        <div class="container">
          <div class="space-y-4">
            <div class="text-lg font-medium">Members</div>
            <div v-if="!isEmpty(team.doc?.users)" class="flex flex-wrap gap-2">
              <Button
                v-for="member in team.doc?.users"
                :key="member.name"
                :label="member.user"
                :disabled="team.loading"
                theme="gray"
                variant="outline"
                @click="removeMember(member.user)"
              >
                <template #suffix>
                  <IconX class="h-3 w-3" />
                </template>
              </Button>
            </div>
            <div v-else class="text-base text-gray-900">
              No members found in team: {{ teamId }}
            </div>
            <Switch
              v-model="ignoreRestrictions"
              size="md"
              label="Bypass restrictions"
              description="Members of this team will be able to bypass any team-wise restriction"
              class="rounded border p-4"
            />
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
            variant="solid"
            class="w-full"
            :disabled="title === teamId"
            @click="renameTeam"
          />
        </div>
      </template>
    </Dialog>
    <Dialog v-model="showDelete" :options="deleteDialogOptions" />
    <Dialog v-model="showAddMember" :options="addMemberDialogOptions">
      <template #body-content>
        <div class="space-y-2">
          <div
            v-for="agent in agentStore.options"
            :key="agent.name"
            class="flex items-center justify-between"
          >
            <div class="flex items-center gap-2">
              <Avatar :label="agent.agent_name" :image="agent.user_image" />
              <div class="text-base">
                {{ agent.agent_name }}
              </div>
            </div>
            <Button
              :disabled="!!team.doc?.users.find((u) => u.user === agent.user)"
              label="Add"
              theme="gray"
              variant="outline"
              @click="addMember(agent.user)"
            />
          </div>
        </div>
      </template>
    </Dialog>
  </span>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import {
  createDocumentResource,
  createResource,
  Avatar,
  Button,
  Dialog,
  Dropdown,
  FormControl,
  Switch,
} from "frappe-ui";
import { isEmpty } from "lodash";
import { AGENT_PORTAL_TEAM_LIST, AGENT_PORTAL_TEAM_SINGLE } from "@/router";
import { useAgentStore } from "@/stores/agent";
import { useError } from "@/composables/error";
import { PageTitle, BreadCrumbs } from "@/components";
import TopBar from "@/components/TopBar.vue";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import IconPlus from "~icons/lucide/plus";
import IconX from "~icons/lucide/x";

const props = defineProps({
  teamId: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const agentStore = useAgentStore();
const showRename = ref(false);
const showDelete = ref(false);
const showAddMember = ref(false);
const team = createDocumentResource({
  doctype: "HD Team",
  name: props.teamId,
  auto: true,
  setValue: {
    onError: useError({ title: "Error updating team" }),
  },
  delete: {
    onSuccess() {
      router.replace({
        name: AGENT_PORTAL_TEAM_LIST,
      });
    },
    onError: useError({ title: "Error deleting team" }),
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
const ignoreRestrictions = computed({
  get() {
    return !!team.doc?.ignore_restrictions;
  },
  set(value: boolean) {
    if (!team.doc) return;
    team.setValue.submit({
      ignore_restrictions: value,
    });
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
const addMemberDialogOptions = { title: "Add member" };
const deleteDialogOptions = {
  title: "Delete team",
  message: `Are you sure you want to delete ${props.teamId}? This action cannot be reversed!`,
  actions: [
    {
      label: "Confirm",
      theme: "red",
      variant: "solid",
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
    onError: useError({ title: "Error renaming team" }),
  });

  r.submit();
}

function addMember(user: string) {
  const users = team.doc.users.concat([{ user }]);
  team.setValue.submit({
    users,
  });
}

function removeMember(member: string) {
  const users = team.doc.users.filter((u) => u.user !== member);
  team.setValue.submit({
    users,
  });
}
</script>
