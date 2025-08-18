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
              :key="user.username"
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
                    :label="user.full_name"
                    size="lg"
                  />
                  <div class="flex flex-col gap-1">
                    <div class="font-semibold text-ink-gray-7">
                      {{ user.full_name }}
                    </div>
                    <div class="text-ink-gray-6">{{ user.email }}</div>
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
              @click="
                () => {
                  showNewAgentsDialog = true;
                  togglePopover();
                }
              "
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
import { watchDebounced } from "@vueuse/core";
import { Avatar, createListResource, Popover } from "frappe-ui";
import { computed, ref } from "vue";

const emit = defineEmits(["addAssignee"]);
const query = ref("");
const showNewAgentsDialog = ref(false);

watchDebounced(
  () => query.value,
  (val) => {
    const filters = {
      full_name: undefined,
      email: undefined,
    };
    const isEmail = val.includes("@") || val.includes(".");
    if (isEmail) {
      filters.email = ["like", `%${val}%`];
    } else {
      filters.full_name = ["like", `%${val}%`];
    }
    usersList.update({
      filters,
    });
    usersList.reload();
  },
  { debounce: 500 }
);

const usersList = createListResource({
  doctype: "User",
  fields: ["name", "email", "full_name", "user_image"],
  start: 0,
  pageLength: 5,
  auto: true,
  transform: (data) => {
    return data
      .map((user) => {
        if (user.full_name == "Administrator") {
          return {
            ...user,
            email: "Administrator",
            user: "Administrator",
          };
        }
        return {
          ...user,
          user: user.email,
        };
      })
      .filter((user) => user.full_name != "Guest");
  },
});

const users = computed(() => {
  return (
    usersList.data?.filter(
      (user) =>
        !assignmentRuleData.value.users.some((u) => u.user === user.email)
    ) || []
  );
});

const addInvitedAgents = (users) => {
  users.forEach((user) => {
    addAssignee({ user });
  });
};

const addAssignee = (user) => {
  const userExists = assignmentRuleData.value.users.some(
    (u) => u.user === user.user
  );
  if (!userExists) {
    assignmentRuleData.value.users.push({
      full_name: user.full_name,
      email: user.email,
      user_image: user.user_image,
      user: user.email,
    });
    emit("addAssignee", user);
  }
};
</script>
