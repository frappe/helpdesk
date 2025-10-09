<template>
  <Combobox :multiple="true">
    <Popover placement="bottom-end">
      <template #target="{ togglePopover }">
        <Button
          variant="subtle"
          icon-left="plus"
          @click="togglePopover()"
          :label="__('Add Assignee')"
        />
      </template>
      <template #body="{ togglePopover }">
        <div class="mt-1 rounded-lg bg-white py-1 text-base shadow-2xl w-60">
          <div class="relative px-1.5 pt-0.5">
            <ComboboxInput
              ref="search"
              class="form-input w-full"
              type="text"
              @change="
                (e) => {
                  query = e.target.value;
                }
              "
              :value="query"
              autocomplete="off"
              :placeholder="__('Search')"
            />
            <button
              class="absolute right-1.5 inline-flex h-7 w-7 items-center justify-center"
              @click="query = ''"
            >
              <FeatherIcon name="x" class="w-4" />
            </button>
          </div>
          <ComboboxOptions class="my-2 max-h-64 overflow-y-auto px-1.5" static>
            <ComboboxOption
              v-show="users.length > 0"
              v-for="user in users"
              :key="user.name"
              :value="user"
              as="template"
              v-slot="{ active }"
              @click="
                (e) => {
                  e.stopPropagation();
                  addAssignee(user);
                }
              "
            >
              <li
                class="flex items-center rounded p-1.5 w-full text-base"
                :class="{ 'bg-gray-100': active }"
              >
                <div class="flex gap-2 items-center w-full select-none">
                  <Avatar
                    :shape="'circle'"
                    :image="user.user_image"
                    :label="user.agent_name"
                    size="lg"
                  />
                  <div class="flex flex-col gap-1">
                    <div class="font-semibold text-ink-gray-7">
                      {{ user.agent_name }}
                    </div>
                    <div class="text-ink-gray-6">{{ user.user }}</div>
                  </div>
                </div>
              </li>
            </ComboboxOption>
            <li
              v-if="users.length == 0"
              class="mt-1.5 rounded-md p-1.5 text-base text-gray-600"
            >
              {{ __("No results found") }}
            </li>
          </ComboboxOptions>
          <div class="border-t p-1.5 pb-0.5">
            <Button
              variant="ghost"
              class="w-full"
              icon-left="plus"
              :label="__('Invite agent')"
              @click="setActiveSettingsTab('Invite Agents')"
            />
          </div>
        </div>
      </template>
    </Popover>
  </Combobox>

  <AddNewAgentsDialog
    :title="__('Add Agents')"
    @close="showNewAgentsDialog = false"
    :modelValue="showNewAgentsDialog"
    :show="showNewAgentsDialog"
    @update:modelValue="showNewAgentsDialog = $event"
    @onAgentsInvited="addInvitedAgents"
  />
</template>

<script setup lang="ts">
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue";
import { assignmentRuleData } from "@/stores/assignmentRules";
import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from "@headlessui/vue";
import { Avatar, Popover } from "frappe-ui";
import { computed, ref } from "vue";
import { setActiveSettingsTab } from "../settingsModal";
import { useAgentStore } from "@/stores/agent";
import { onMounted } from "vue";

const emit = defineEmits(["addAssignee"]);
const query = ref("");
const showNewAgentsDialog = ref(false);
const { agents } = useAgentStore();

const users = computed(() => {
  let filteredAgents =
    agents.data?.filter(
      (user) =>
        !assignmentRuleData.value.users.some((u) => u.user === user.user)
    ) || [];

  if (query.value) {
    const val = query.value.toLowerCase();
    const isEmail = val.includes("@") || val.includes(".");
    filteredAgents = filteredAgents.filter((user) => {
      if (isEmail) {
        return user.email?.toLowerCase().includes(val);
      } else {
        return user.full_name?.toLowerCase().includes(val);
      }
    });
  }
  return filteredAgents;
});

const addInvitedAgents = (users) => {
  users.forEach((user) => {
    addAssignee({ user });
  });
};

const addAssignee = (user) => {
  assignmentRuleData.value.users.push({
    user: user.user,
  });
  emit("addAssignee", user);
};

onMounted(() => {
  if (agents.loading || agents.data?.length || agents.list.promise) {
    return;
  }
  agents.fetch();
});
</script>
