<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-1 justify-center -ml-[16px]">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="teamName"
            size="md"
            @click="() => emit('update:step', 'team-list')"
            class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
          />
        </div>
      </div>
    </template>
    <template #header-actions>
      <Dropdown placement="right" :options="options">
        <Button variant="ghost">
          <template #icon>
            <LucideMoreHorizontal class="h-4 w-4" />
          </template>
        </Button>
      </Dropdown>
    </template>
    <template #header-bottom>
      <!-- Add member -->
      <div class="flex gap-2 items-center">
        <!-- Form control for search -->
        <div class="flex flex-col gap-1.5 w-full">
          <div class="flex gap-2">
            <div class="flex flex-1">
              <AgentSelector
                v-model="invitees"
                :existing-agents="teamMembers.map((m) => m.name)"
              />
            </div>
            <Button
              label="Add Member"
              variant="solid"
              :disabled="!invitees.length"
              @click="addMember(invitees)"
              class="h-8"
            >
              <template #prefix>
                <LucidePlus class="h-4 w-4 stroke-1.5" />
              </template>
            </Button>
          </div>
        </div>
      </div>
    </template>
    <template #content>
      <div class="w-full h-full" v-if="teamMembers?.length > 0">
        <div class="grid grid-cols-8 items-center gap-3 text-sm text-gray-600">
          <div class="col-span-6 text-p-sm">
            {{ __("Members ({0})", teamMembers.length) }}
          </div>
        </div>
        <hr class="mt-2" />
        <div v-for="(member, idx) in teamMembers" :key="member.name">
          <div class="grid grid-cols-8 items-center gap-4 group">
            <div class="w-full p-2 pl-0 col-span-8">
              <AgentCard :agent="member" class="!py-0">
                <template #right>
                  <Dropdown
                    :options="memberDropdownOptions(member)"
                    placement="right"
                  >
                    <Button
                      icon="more-horizontal"
                      variant="ghost"
                      @click="isConfirmingDelete = false"
                    />
                  </Dropdown>
                </template>
              </AgentCard>
            </div>
          </div>
          <hr v-if="member !== teamMembers.at(-1)" />
        </div>
      </div>
      <div
        v-else
        class="flex flex-col items-center justify-center gap-4 h-full"
      >
        <div
          class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
        >
          <UserIcon class="size-6 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-base font-medium text-ink-gray-6">
            {{ __("No members found") }}
          </div>
          <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
            {{ __("Add members to this team to get started.") }}
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <Dialog v-model="showDelete" :options="{ title: 'Delete team' }">
    <template #body-content>
      <p class="text-p-base text-ink-gray-7">
        {{
          __(
            "Are you sure you want to delete this team? This action cannot be reversed!"
          )
        }}
      </p>
      <Button
        variant="solid"
        class="mt-4 float-right"
        :label="__('Confirm')"
        theme="red"
        @click="
          () => {
            team.delete.submit();
            showDelete = false;
            emit('update:step', 'team-list');
          }
        "
      />
    </template>
  </Dialog>
  <Dialog v-model="showRename" :options="renameDialogOptions">
    <template #body-content>
      <FormControl
        v-model="_teamName"
        :label="__('Title')"
        :placeholder="__('Product Experts')"
        maxlength="50"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { useAgentStore } from "@/stores/agent";
import { assignmentRulesActiveScreen } from "@/stores/assignmentRules";
import { useConfigStore } from "@/stores/config";
import { useUserStore } from "@/stores/user";
import { __ } from "@/translation";
import { TeamListResourceSymbol } from "@/types";
import { ConfirmDelete } from "@/utils";
import {
  Button,
  createDocumentResource,
  createResource,
  Dialog,
  Dropdown,
  toast,
  Tooltip,
} from "frappe-ui";
import { computed, h, inject, markRaw, onMounted, ref } from "vue";
import LucideLock from "~icons/lucide/lock";
import Settings from "~icons/lucide/settings-2";
import LucideUnlock from "~icons/lucide/unlock";
import UserIcon from "~icons/lucide/user";
import AgentCard from "../AgentCard.vue";
import { setActiveSettingsTab } from "../settingsModal";
import AgentSelector from "./components/AgentSelector.vue";

const props = defineProps<{
  teamName: string;
}>();

interface E {
  (event: "update:step", step: string, team?: string): void;
}
const emit = defineEmits<E>();

const { getUser } = useUserStore();
const { agents } = useAgentStore();
const teamsList = inject(TeamListResourceSymbol);

const { teamRestrictionApplied } = useConfigStore();
const invitees = ref<string[]>([]);

const _teamName = ref(props.teamName);
const team = createDocumentResource({
  doctype: "HD Team",
  name: props.teamName,
  auto: true,
  delete: {
    onSuccess() {
      toast.success(__("Team deleted"));
      emit("update:step", "team-list");
    },
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

const teamMembers = computed(() => {
  let users = team.doc?.users || [];
  return users.map((user) => {
    let _user = getUser(user.user);
    return {
      name: user.user,
      user_image: _user.user_image,
      agent_name: _user.full_name,
    };
  });
});

function removeMemberFromTeam(member: string) {
  const users = team.doc?.users?.filter((u) => u.user !== member);
  team.setValue.submit({
    users,
  });
}

function addMember(users: string[]) {
  const _users = team.doc.users.concat(users.map((user) => ({ user })));
  team.setValue.submit({
    users: _users,
  });
  invitees.value = [];
}

const showRename = ref(false);

const renameDialogOptions = {
  title: __("Rename team"),
  message: __("Enter the new name for the team"),
  actions: [
    {
      label: __("Confirm"),
      variant: "solid",
      loading: team.loading,
      onClick: ({ close }) => {
        renameTeam(close);
      },
    },
  ],
};

function renameTeam(close) {
  const r = createResource({
    url: "frappe.client.rename_doc",
    makeParams() {
      return {
        doctype: "HD Team",
        old_name: props.teamName,
        new_name: _teamName.value,
      };
    },
    validate(params) {
      if (!params.new_name) return __("New title is required");
      if (params.new_name === params.old_name)
        return __("New and old title cannot be same");
    },
    onSuccess() {
      teamsList.reload();
      toast.success(__("Team renamed"));
      close();
      emit("update:step", "team-list");
    },
  });

  r.submit();
}

const showDelete = ref(false);

const options = [
  {
    label: __("View Assignment rule"),
    icon: markRaw(h(Settings, { class: "rotate-90" })),
    onClick: () => {
      assignmentRulesActiveScreen.value = {
        data: { name: team.doc?.assignment_rule },
        screen: "view",
      };
      setActiveSettingsTab("Assignment Rules");
    },
  },
  {
    label: __("Rename"),
    icon: "edit-3",
    onClick: () => (showRename.value = !showRename.value),
  },
  {
    condition: () => teamRestrictionApplied,
    label: team.doc?.ignore_restrictions
      ? __("Disable Bypass Restrictions")
      : __("Enable Bypass Restrictions"),
    component: () =>
      h(
        Tooltip,
        {
          text: ignoreRestrictions.value
            ? __(
                "Members of this team will see the tickets assigned to this team only"
              )
            : __(
                "Members of this team will be able to see the tickets assigned to all the teams"
              ),
        },
        {
          default: () => [
            //create a div with 2 columns, one for icon and one for label
            h(
              "div",
              {
                class:
                  "flex items-center gap-2 p-2 cursor-pointer hover:bg-gray-100 rounded",
                onClick: () =>
                  (ignoreRestrictions.value = !ignoreRestrictions.value),
              },
              [
                h(team.doc?.ignore_restrictions ? LucideLock : LucideUnlock, {
                  class: "h-4 w-4 text-gray-700",
                  stroke: "currentColor",
                  "aria-hidden": "true",
                }),
                h(
                  "span",
                  {
                    class: "whitespace-nowrap text-ink-gray-7 text-p-base",
                  },
                  [
                    team.doc?.ignore_restrictions
                      ? __("Access only this team's tickets")
                      : __("Access all team tickets"),
                  ]
                ),
              ]
            ),
          ],
        }
      ),
  },
  {
    label: __("Delete"),
    component: h(Button, {
      label: __("Delete"),
      variant: "ghost",
      iconLeft: "trash-2",
      theme: "red",
      style: "width: 100%; justify-content: flex-start;",
      onClick: () => {
        showDelete.value = !showDelete.value;
      },
    }),
  },
];

const isConfirmingDelete = ref(false);

const memberDropdownOptions = (member) => {
  return ConfirmDelete({
    onConfirmDelete: () => removeMemberFromTeam(member.name),
    isConfirmingDelete,
  });
};

onMounted(() => {
  if (agents.loading || agents.data?.length || agents.list.promise) {
    return;
  }
  agents.fetch();
});
</script>
