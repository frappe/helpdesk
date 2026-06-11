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
      <div class="flex items-center gap-4">
        <div class="flex items-center justify-between gap-2 cursor-pointer">
          <Switch v-model="teamEnabled" v-if="!team.loading" />
          <span class="text-sm text-ink-gray-7 font-medium">
            {{ __("Enabled") }}
          </span>
        </div>
        <Dropdown placement="right" :options="options">
          <Button variant="ghost">
            <template #icon>
              <LucideMoreHorizontal class="h-4 w-4" />
            </template>
          </Button>
        </Dropdown>
      </div>
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
        <div
          class="grid grid-cols-8 items-center gap-3 text-sm text-ink-gray-5"
        >
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
                    v-if="teamMembers.length > 1"
                    :options="memberDropdownOptions(member)"
                    placement="right"
                  >
                    <Button
                      icon="lucide-more-horizontal"
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
  <RenameTeamModal
    v-model="showRename"
    @onRename="
      () => {
        teamsList.reload();
        emit('update:step', 'team-list');
      }
    "
  />
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
  Dropdown,
  Switch,
  toast,
} from "frappe-ui";
import { computed, h, inject, markRaw, onMounted, ref } from "vue";
import RenameTeamModal from "./RenameTeamModal.vue";
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

const team = createDocumentResource({
  doctype: "HD Team",
  name: props.teamName,
  auto: true,
  delete: {
    onSuccess() {
      toast.success(__("Team deleted successfully."));
      emit("update:step", "team-list");
    },
  },
});

const teamEnabled = computed({
  get() {
    return !team.doc?.disabled;
  },
  set(value: boolean) {
    if (!team.doc) return;
    team.doc.disabled = !value;
    team.setValue.submit(
      {
        disabled: !value,
      },
      {
        onSuccess: () => {
          toast.success(
            value
              ? __("Team enabled successfully.")
              : __("Team disabled successfully.")
          );
          team.reload();
        },
      }
    );
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

const showRename = ref({
  show: false,
  teamName: props.teamName,
});

const isConfirmingTeamDelete = ref(false);

const options = computed(() => [
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
    icon: "lucide-edit-3",
    onClick: () => {
      showRename.value = { show: true, teamName: props.teamName };
    },
  },
  ...(teamRestrictionApplied
    ? [
        {
          label: ignoreRestrictions.value
            ? __("Access only this team's tickets")
            : __("Access all team tickets"),
          icon: markRaw(ignoreRestrictions.value ? LucideLock : LucideUnlock),
          onClick: () => {
            ignoreRestrictions.value = !ignoreRestrictions.value;
            toast.success(
              ignoreRestrictions.value
                ? __("Team can now access all tickets.")
                : __("Team will only see their own tickets.")
            );
          },
        },
      ]
    : []),
  ...ConfirmDelete({
    isConfirmingDelete: isConfirmingTeamDelete,
    onConfirmDelete: () => team.delete.submit(),
  }),
]);

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
