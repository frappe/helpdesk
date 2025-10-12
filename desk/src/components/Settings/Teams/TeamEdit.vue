<template>
  <!-- Header -->
  <div class="px-10 py-8 sticky top-0">
    <SettingsLayoutHeader>
      <template #title>
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center gap-1 justify-center -ml-[16px]">
            <Button
              variant="ghost"
              icon-left="chevron-left"
              :label="teamName"
              size="md"
              @click="() => emit('update:step', 'team-list')"
              class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-xl hover:opacity-70 !pr-0"
            />
          </div>
        </div>
      </template>
      <template #actions>
        <Dropdown placement="right" :options="options">
          <Button variant="ghost">
            <template #icon>
              <LucideMoreHorizontal class="h-4 w-4" />
            </template>
          </Button>
        </Dropdown>
      </template>
      <template #bottom-section>
        <!-- Add member -->
        <div class="flex flex-col">
          <div class="flex gap-2 items-end">
            <!-- Form control for search -->
            <Link
              doctype="HD Agent"
              class="form-control flex-1"
              placeholder="Search members"
              v-model="search"
              :hide-me="true"
              :filters="agentFilters"
            >
              <template #prefix>
                <LucideSearch class="h-4 w-4 text-gray-500 mr-2" />
              </template>
              <template #item-label="{ option }">
                <div class="flex items-center justify-between !w-full">
                  <div class="flex items-center gap-1">
                    <Avatar
                      :label="option.label || option.value"
                      :image="getUser(option.label)?.user_image"
                      size="sm"
                    />
                    <p>{{ getUser(option.label)?.full_name || "User" }}</p>
                  </div>
                  <p class="text-gray-600 text-sm">
                    {{ option.label }}
                  </p>
                </div>
              </template>
            </Link>
            <Button
              label="Add"
              variant="solid"
              :disabled="!search"
              @click="addMember(search)"
            >
              <template #prefix>
                <LucidePlus class="h-4 w-4 stroke-1.5" />
              </template>
            </Button>
          </div>
        </div>
      </template>
    </SettingsLayoutHeader>
  </div>

  <!-- Member List -->
  <div class="px-10 pb-8 overflow-y-auto" v-if="teamMembers?.length > 0">
    <div class="w-full h-full">
      <div class="grid grid-cols-8 items-center gap-3 text-sm text-gray-600">
        <div class="col-span-6 text-p-sm">
          Members ({{ teamMembers.length }})
        </div>
      </div>
      <hr class="mt-2" />
      <div v-for="member in teamMembers" :key="member.name">
        <div class="grid grid-cols-8 items-center gap-4 group">
          <div class="w-full p-2 pl-0 col-span-8">
            <AgentCard :agent="member" class="!py-0">
              <template #right>
                <Dropdown :options="memberDropdownOptions(member)">
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
        <hr />
      </div>
    </div>
  </div>
  <div
    v-else
    class="flex flex-col items-center justify-center gap-4 p-4 mt-7 h-[500px]"
  >
    <div
      class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
    >
      <UserIcon class="size-6 text-ink-gray-6" />
    </div>
    <div class="flex flex-col items-center gap-1">
      <div class="text-base font-medium text-ink-gray-6">No members found</div>
      <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
        Add members to this team to get started.
      </div>
    </div>
  </div>

  <Dialog v-model="showDelete" :options="{ title: 'Delete team' }">
    <template #body-content>
      <p class="text-p-base text-ink-gray-7">
        Are you sure you want to delete this team? This action cannot be
        reversed!
      </p>
      <Button
        variant="solid"
        class="mt-4 float-right"
        label="Confirm"
        theme="red"
        @click="
          () => {
            team.delete.submit();
            showDelete = false;
          }
        "
      />
    </template>
  </Dialog>
  <Dialog v-model="showRename" :options="renameDialogOptions">
    <template #body-content>
      <FormControl
        v-model="_teamName"
        label="Title"
        placeholder="Product Experts"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import Link from "@/components/frappe-ui/Link.vue";
import { useConfigStore } from "@/stores/config";
import { useUserStore } from "@/stores/user";
import {
  Avatar,
  Button,
  createDocumentResource,
  createResource,
  Dialog,
  toast,
  Tooltip,
} from "frappe-ui";
import { computed, h, markRaw, ref } from "vue";
import LucideLock from "~icons/lucide/lock";
import LucideUnlock from "~icons/lucide/unlock";
import AgentCard from "../AgentCard.vue";
import Settings from "~icons/lucide/settings-2";
import { assignmentRulesActiveScreen } from "@/stores/assignmentRules";
import { setActiveSettingsTab } from "../settingsModal";
import UserIcon from "~icons/lucide/user";
import { ConfirmDelete } from "@/utils";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";

const props = defineProps<{
  teamName: string;
}>();

interface E {
  (event: "update:step", value: string): void;
}
const emit = defineEmits<E>();

const { getUser } = useUserStore();
const { teamRestrictionApplied } = useConfigStore();
const _teamName = ref(props.teamName);
const team = createDocumentResource({
  doctype: "HD Team",
  name: props.teamName,
  auto: true,
  delete: {
    onSuccess() {
      toast.success("Team deleted");
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
const search = ref("");

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

const agentFilters = computed(() => {
  return {
    name: ["not in", teamMembers.value.map((user) => user.name)],
  };
});

function removeMemberFromTeam(member: string) {
  const users = team.doc?.users?.filter((u) => u.user !== member);
  team.setValue.submit({
    users,
  });
}

function addMember(user: string) {
  const users = team.doc.users.concat([{ user }]);
  team.setValue.submit({
    users,
  });
  search.value = "";
}

const showRename = ref(false);

const renameDialogOptions = {
  title: "Rename team",
  message: "Enter the new name for the team",
  actions: [
    {
      label: "Confirm",
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
      if (!params.new_name) return "New title is required";
      if (params.new_name === params.old_name)
        return "New and old title cannot be same";
    },
    onSuccess() {
      toast.success("Team renamed");
      close();
      emit("update:step", "team-list");
    },
  });

  r.submit();
}

const showDelete = ref(false);
const deleteDialogOptions = {
  title: "Delete team",
  message: `Are you sure you want to delete this team? This action cannot be reversed!`,
  actions: [
    {
      label: "Confirm",
      variant: "solid",
      onClick: (ctx) => {
        team.delete.submit();
        ctx.close();
      },
    },
  ],
};

const options = [
  {
    label: "View Assignment rule",
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
    label: "Rename",
    icon: "edit-3",
    onClick: () => (showRename.value = !showRename.value),
  },
  {
    condition: () => teamRestrictionApplied,
    label: team.doc?.ignore_restrictions
      ? "Disable Bypass Restrictions"
      : "Enable Bypass Restrictions",
    component: () =>
      h(
        Tooltip,
        {
          text: ignoreRestrictions.value
            ? "Members of this team will see the tickets assigned to this team only"
            : "Members of this team will be able to see the tickets assigned to all the teams",
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
                      ? "Access only this team's tickets"
                      : "Access all team tickets",
                  ]
                ),
              ]
            ),
          ],
        }
      ),
  },
  {
    label: "Delete",
    component: h(Button, {
      label: "Delete",
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
</script>

<style scoped></style>
