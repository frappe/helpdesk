<template>
  <div>
    <div class="w-full h-full flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between mb-7">
        <Breadcrumbs :items="breadcrumbs" class="-ml-0.5" />
        <Button icon="trash-2" variant="ghost" theme="red" />
      </div>
      <div class="flex flex-col gap-4">
        <!-- Name -->
        <FormControl type="text" v-model="_teamName" label="Team Name" />
        <!-- Add member -->
        <div class="flex gap-2 items-end">
          <!-- Form control for search -->
          <Link
            doctype="HD Agent"
            class="form-control flex-1"
            placeholder="Add members"
            v-model="search"
            label="Members"
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

        <!-- Member List -->
        <div
          class="flex flex-col divide-y divide-gray-200"
          v-if="teamMembers.length"
        >
          <div
            v-for="(member, idx) in teamMembers"
            :key="member.user"
            class="group py-2"
          >
            <AgentCard :agent="member" class="!py-0">
              <template #right>
                <Button
                  variant="ghost"
                  @click.stop="() => removeMemberFromTeam(member.name)"
                  class="opacity-0 group-hover:opacity-100"
                >
                  <template #icon>
                    <LucideX class="h-4 w-4" />
                  </template>
                </Button>
              </template>
            </AgentCard>
          </div>
        </div>
        <div v-else class="flex items-center justify-center h-full">
          <p class="text-p-base text-gray-500">No members found</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from "@/stores/user";
import { Breadcrumbs, createDocumentResource, FormControl } from "frappe-ui";
import { computed, ref } from "vue";

import Link from "@/components/frappe-ui/Link.vue";
import Avatar from "frappe-ui/src/components/Avatar.vue";
import AgentCard from "../AgentCard.vue";

const props = defineProps<{
  teamName: string;
}>();

interface E {
  (event: "update:step", value: string): void;
}
const emit = defineEmits<E>();

const { getUser } = useUserStore();

const team = createDocumentResource({
  doctype: "HD Team",
  name: props.teamName,
  auto: true,
});

const _teamName = ref(props.teamName);
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

const breadcrumbs = computed(() => {
  return [
    {
      label: "Teams",
      onClick: () => {
        emit("update:step", "team-list");
      },
    },
    { label: props.teamName },
  ];
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
</script>

<style scoped></style>
