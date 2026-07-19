<template>
  <SettingsLayoutBase
    :title="__('Saved Replies')"
    :description="
      __(
        'Manage pre-defined responses that can be used to respond to customer queries.'
      )
    "
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        @click="goToNew()"
        icon-left="lucide-plus"
      />
    </template>
    <template #header-bottom>
      <div class="flex items-center gap-2 justify-between">
        <div class="relative w-full">
          <TextInput
            :model-value="savedRepliesSearchQuery"
            @update:model-value="savedRepliesSearchQuery = $event"
            :placeholder="__('Search')"
            type="text"
            :debounce="300"
          >
            <template #prefix>
              <LucideSearch class="size-4" />
            </template>
          </TextInput>
          <Button
            v-if="savedRepliesSearchQuery"
            icon="lucide-x"
            variant="ghost"
            @click="savedRepliesSearchQuery = ''"
            class="absolute right-1 top-1/2 -translate-y-1/2"
          />
        </div>
        <Dropdown :options="filterOptions" placement="right">
          <template #default="{ open }">
            <Button
              :label="activeFilter"
              class="flex items-center justify-between w-fit p-4"
            >
              <template #suffix>
                <FeatherIcon
                  :name="open ? 'chevron-up' : 'chevron-down'"
                  class="h-4"
                />
              </template>
            </Button>
          </template>
          <template #item-label="{ item }">
            <button
              class="group flex text-ink-gray-6 gap-4 w-full justify-between items-center rounded text-base"
              @click="item.onSelect"
            >
              <div class="flex items-center justify-between flex-1">
                <span class="whitespace-nowrap">
                  {{ item.label }}
                </span>
                <FeatherIcon
                  v-if="activeFilter === item.value"
                  name="check"
                  class="size-4 text-ink-gray-7"
                />
              </div>
            </button>
          </template>
        </Dropdown>
      </div>
    </template>
    <template #content>
      <div
        v-if="savedRepliesListResource?.list?.loading"
        class="flex items-center justify-center h-[stretch] absolute w-[stretch] left-0 top-5.5"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <EmptyState
        v-if="
          !savedRepliesListResource?.list?.loading &&
          !savedRepliesListResource?.data?.length
        "
        variant="badge"
        :icon="SavedReplyIcon"
        :title="__('No saved replies found')"
        :description="__('Add one to get started.')"
      />
      <div
        v-if="
          !savedRepliesListResource?.list?.loading &&
          savedRepliesListResource?.data?.length
        "
        class="-ml-2"
      >
        <div
          class="grid grid-cols-12 items-center gap-3 text-sm text-ink-gray-5 ml-2"
        >
          <div class="col-span-7">{{ __("Title") }}</div>
          <div class="col-span-2">{{ __("Owner") }}</div>
          <div class="col-span-3">{{ __("Scope") }}</div>
        </div>
        <hr class="mt-2 mx-2" />
        <div
          v-for="(savedReply, index) in savedRepliesListResource?.data"
          :key="savedReply.name"
        >
          <div
            class="grid grid-cols-12 items-center gap-4 cursor-pointer hover:bg-surface-sidebar rounded"
          >
            <div
              @click="
                savedRepliesActiveScreen = {
                  screen: 'view',
                  data: savedReply,
                }
              "
              class="w-full px-2 flex flex-col justify-center h-12.5 col-span-7 min-w-0"
            >
              <div class="text-base-medium text-ink-gray-7 w-full truncate">
                {{ savedReply.title }}
              </div>
            </div>
            <div
              class="flex items-center gap-1.5 text-sm text-ink-gray-7 col-span-2 min-w-0"
            >
              <Avatar
                :label="
                  getUser(savedReply.owner)?.full_name || savedReply.owner
                "
                :image="getUser(savedReply.owner)?.user_image"
                size="xs"
                class="shrink-0"
              />
              <span class="truncate">{{
                getUser(savedReply.owner)?.full_name
              }}</span>
            </div>
            <div
              class="flex justify-between items-center w-full pr-2 col-span-3"
            >
              <div class="flex items-center gap-1 text-sm text-ink-gray-7">
                <component
                  :is="getScopeIcon(savedReply.scope)"
                  class="size-4"
                />
                {{ savedReply.scope }}
              </div>
              <Dropdown
                placement="right"
                :options="dropdownOptions(savedReply)"
              >
                <Button
                  icon="lucide-more-horizontal"
                  variant="ghost"
                  @click="isConfirmingDelete = false"
                  class="mr-2"
                />
              </Dropdown>
            </div>
          </div>
          <hr
            v-if="index !== savedRepliesListResource.data.length - 1"
            class="mx-2"
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <Dialog
    :title="__('Duplicate Saved reply')"
    v-model:open="duplicateDialog.show"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          :label="__('New Saved reply Name')"
          type="text"
          v-model="duplicateDialog.newTitle"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          variant="subtle"
          :label="__('Close')"
          @click="duplicateDialog.show = false"
        />
        <Button variant="solid" :label="__('Duplicate')" @click="duplicate()" />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useConfigStore } from "@/stores/config";
import { __ } from "@/translation";
import { ConfirmDelete } from "@/utils";
import {
  Avatar,
  Button,
  call,
  Dropdown,
  FeatherIcon,
  LoadingIndicator,
  TextInput,
  toast,
} from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, inject, ref, Ref, watch } from "vue";
import EmptyState from "@/components/EmptyState.vue";
import GlobeIcon from "~icons/lucide/globe";
import UserIcon from "~icons/lucide/user";
import UsersIcon from "~icons/lucide/users";
import { useUserStore } from "../../../stores/user";
import { SavedReply, SavedReplyListResourceSymbol } from "../../../types";
import SavedReplyIcon from "../../icons/SavedReplyIcon.vue";
import SettingsLayoutBase from "../../layouts/SettingsLayoutBase.vue";
import { activeFilter } from "./savedReplies";

const { getUser } = useUserStore();
const { disableGlobalScopeForSavedReplies, teamRestrictionApplied } =
  storeToRefs(useConfigStore());

const savedRepliesSearchQuery = inject<Ref<string>>("savedRepliesSearchQuery");
const savedRepliesActiveScreen = inject<any>("savedRepliesActiveScreen");
const duplicateDialog = ref({
  show: false,
  name: "",
  title: "",
  newTitle: "",
});
const savedRepliesList = ref([]);

const goToNew = () => {
  savedRepliesActiveScreen.value = {
    screen: "view",
    data: {
      scope: activeFilter.value
        ? activeFilter.value === "All"
          ? "Personal"
          : activeFilter.value
        : "Personal",
    },
  };
};

const isConfirmingDelete = ref(false);

const savedRepliesListResource = inject(SavedReplyListResourceSymbol);

const dropdownOptions = (savedReply: SavedReply) => [
  {
    label: __("Duplicate"),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: savedReply.name,
        title: savedReply.title,
        newTitle: `${savedReply.title} (Copy)`,
      };
    },
    icon: "lucide-copy",
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteSavedReply(savedReply),
    isConfirmingDelete,
  }),
];

const deleteSavedReply = (savedReply: SavedReply) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  savedRepliesListResource?.delete.submit(savedReply.name, {
    onSuccess: () => {
      toast.success(__("Saved reply deleted successfully."));
    },
  });
};

const duplicate = async () => {
  await call("frappe.client.get", {
    doctype: "HD Saved Reply",
    name: duplicateDialog.value.name,
  }).then((data: SavedReply) => {
    savedRepliesListResource?.insert.submit(
      {
        ...data,
        title: duplicateDialog.value.newTitle,
      },
      {
        onSuccess: (data) => {
          toast.success(__("Saved reply duplicated successfully."));
          duplicateDialog.value = {
            show: false,
            name: "",
            title: "",
            newTitle: "",
          };
          savedRepliesActiveScreen.value = {
            screen: "view",
            data: { name: data.name },
          };
        },
      }
    );
  });
};

const filterOptions = computed(() => {
  const options = [
    {
      label: __("All"),
      value: "All",
      onSelect: () => {
        applyFilter("All");
      },
    },
    {
      label: __("Personal"),
      value: "Personal",
      onSelect: () => {
        applyFilter("Personal");
      },
    },
    {
      label: __("My Team"),
      value: "Team",
      onSelect: () => {
        applyFilter("Team");
      },
    },
    {
      label: __("Global"),
      value: "Global",
      onSelect: () => {
        applyFilter("Global");
      },
    },
  ];
  if (teamRestrictionApplied.value && disableGlobalScopeForSavedReplies.value) {
    options.pop();
  }
  return options;
});

const applyFilter = (scope: string) => {
  if (!savedRepliesListResource) return;
  activeFilter.value = scope;
  savedRepliesListResource.filters = {
    ...savedRepliesListResource?.filters,
    scope: scope == "All" ? undefined : ["=", scope],
  };
  savedRepliesListResource.list.reload();
};

const getScopeIcon = (scope: string) => {
  const icons = [
    {
      label: __("Personal"),
      icon: UserIcon,
    },
    {
      label: __("Team"),
      icon: UsersIcon,
    },
    {
      label: __("Global"),
      icon: GlobeIcon,
    },
  ];
  return icons.find((x) => x.label === scope)?.icon;
};

watch(
  () => savedRepliesSearchQuery?.value,
  (newValue) => {
    if (!savedRepliesListResource) return;

    savedRepliesListResource.filters = {
      ...savedRepliesListResource.filters,
      title: ["like", `%${newValue}%`],
    };
    savedRepliesListResource.list.reload();
  }
);
</script>
