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
        icon-left="plus"
      />
    </template>
    <template #header-bottom>
      <div class="flex items-center gap-2 justify-between">
        <div class="relative w-full">
          <Input
            :model-value="savedRepliesSearchQuery"
            @input="savedRepliesSearchQuery = $event"
            :placeholder="__('Search')"
            type="text"
            class="bg-white hover:bg-white focus:ring-0 border-outline-gray-2"
            icon-left="search"
            debounce="300"
            inputClass="p-4 pr-12"
          />
          <Button
            v-if="savedRepliesSearchQuery"
            icon="x"
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
          <template #item="{ item }">
            <button
              class="group flex text-ink-gray-6 gap-4 h-7 w-full justify-between items-center rounded p-2 text-base hover:bg-surface-gray-3"
              @click="item.onClick"
            >
              <div class="flex items-center justify-between flex-1">
                <span class="whitespace-nowrap">
                  {{ item.label }}
                </span>
                <FeatherIcon
                  v-if="activeFilter === item.label"
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
        v-if="savedRepliesListResource.loading"
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div
        v-if="!savedRepliesListResource.loading && !savedRepliesList?.length"
        class="flex flex-col items-center justify-center gap-4 grow"
      >
        <div
          class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
        >
          <LucideCloudLightning class="size-6 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-base font-medium text-ink-gray-6">
            {{ __("No Saved reply found") }}
          </div>
          <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
            {{ __("Add your first Saved reply to get started.") }}
          </div>
        </div>
        <Button
          :label="__('Add Saved reply')"
          variant="outline"
          icon-left="plus"
          @click="goToNew()"
        />
      </div>
      <div v-if="savedRepliesList?.length" class="-ml-2">
        <div
          class="grid grid-cols-12 items-center gap-3 text-sm text-gray-600 ml-2"
        >
          <div class="col-span-7">{{ __("Name") }}</div>
          <div class="col-span-2">{{ __("Owner") }}</div>
          <div class="col-span-3">{{ __("Scope") }}</div>
        </div>
        <hr class="mt-2 mx-2" />
        <div
          v-for="(savedReply, index) in savedRepliesList"
          :key="savedReply.name"
        >
          <div
            class="grid grid-cols-12 items-center gap-4 cursor-pointer hover:bg-gray-50 rounded"
          >
            <div
              @click="
                savedRepliesActiveScreen = {
                  screen: 'view',
                  data: savedReply,
                }
              "
              class="w-full px-2 flex flex-col justify-center h-12.5 col-span-7"
            >
              <div
                class="text-base text-ink-gray-7 font-medium w-full truncate"
              >
                {{ savedReply.name }}
              </div>
            </div>
            <div
              class="flex items-center gap-1.5 text-sm text-ink-gray-7 truncate col-span-2"
            >
              <Avatar
                :name="getUser(savedReply.owner)?.full_name || savedReply.owner"
                :image="getUser(savedReply.owner)?.user_image"
                size="xs"
              />
              {{ getUser(savedReply.owner)?.full_name }}
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
                  icon="more-horizontal"
                  variant="ghost"
                  @click="isConfirmingDelete = false"
                  class="mr-2"
                />
              </Dropdown>
            </div>
          </div>
          <hr v-if="index !== savedRepliesList.length - 1" class="mx-2" />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <Dialog
    :options="{ title: __('Duplicate Saved reply') }"
    v-model="duplicateDialog.show"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :label="__('New Saved reply Name')"
          type="text"
          v-model="duplicateDialog.newName"
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
import {
  Avatar,
  Button,
  call,
  createResource,
  Dropdown,
  FeatherIcon,
  Input,
  LoadingIndicator,
  toast,
} from "frappe-ui";
import { computed, inject, ref, Ref, watch } from "vue";
import { __ } from "@/translation";
import { ConfirmDelete } from "@/utils";
import LucideCloudLightning from "~icons/lucide/cloud-lightning";
import SettingsLayoutBase from "../../layouts/SettingsLayoutBase.vue";
import { activeFilter } from "./savedReplies";
import { useUserStore } from "../../../stores/user";
import UserIcon from "~icons/lucide/user";
import UsersIcon from "~icons/lucide/users";
import GlobeIcon from "~icons/lucide/globe";

const { getUser } = useUserStore();

const savedRepliesSearchQuery = inject<Ref<string>>("savedRepliesSearchQuery");
const savedRepliesActiveScreen = inject<any>("savedRepliesActiveScreen");
const duplicateDialog = ref({
  show: false,
  name: "",
  newName: "",
});
const savedRepliesList = ref([]);

const goToNew = () => {
  savedRepliesActiveScreen.value = {
    screen: "view",
    data: null,
  };
};

const isConfirmingDelete = ref(false);

const savedRepliesListResource = createResource({
  url: "helpdesk.api.saved_replies.get_saved_replies",
  params: {
    scope: activeFilter.value,
  },
  onSuccess: (data) => {
    savedRepliesList.value = data;
  },
  auto: true,
});

const dropdownOptions = (savedReply) => [
  {
    label: __("Duplicate"),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: savedReply.name,
        newName: `${savedReply.name} (Copy)`,
      };
    },
    icon: "copy",
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteSavedReply(savedReply),
    isConfirmingDelete,
  }),
];

const deleteSavedReply = (savedReply) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  createResource({
    url: "frappe.client.delete",
    params: {
      doctype: "Email Template",
      name: savedReply.name,
    },
    auto: true,
    onSuccess: () => {
      savedRepliesListResource.reload();
      toast.success(__("Saved reply deleted"));
    },
  });
};

const duplicate = async () => {
  await call("frappe.client.get", {
    doctype: "Email Template",
    name: duplicateDialog.value.name,
  }).then((data) => {
    createResource({
      url: "frappe.client.insert",
      params: {
        doc: {
          ...data,
          doctype: "Email Template",
          name: duplicateDialog.value.newName,
        },
      },
      auto: true,
      onSuccess: (data) => {
        toast.success(__("Saved reply duplicated"));
        duplicateDialog.value = {
          show: false,
          name: "",
          newName: "",
        };
        savedRepliesActiveScreen.value = {
          screen: "view",
          data: { name: data.name },
        };
      },
    });
  });
};

const filterOptions = computed(() => [
  {
    label: "All",
    value: "All",
    onClick: () => {
      activeFilter.value = "All";
      savedRepliesListResource.submit({
        scope: "All",
      });
    },
  },
  {
    label: "Personal",
    value: "Personal",
    onClick: () => {
      activeFilter.value = "Personal";
      savedRepliesListResource.submit({
        scope: "Personal",
      });
    },
  },
  {
    label: "My Team",
    value: "My Team",
    onClick: () => {
      activeFilter.value = "My Team";
      savedRepliesListResource.submit({
        scope: "My Team",
      });
    },
  },
  {
    label: "Global",
    value: "Global",
    onClick: () => {
      activeFilter.value = "Global";
      savedRepliesListResource.submit({
        scope: "Global",
      });
    },
  },
]);

const getScopeIcon = (scope: string) => {
  const scopes = [
    {
      name: "Personal",
      icon: UserIcon,
    },
    {
      name: "Team",
      icon: UsersIcon,
    },
    {
      name: "Global",
      icon: GlobeIcon,
    },
  ];
  return scopes.find((x) => x.name === scope)?.icon;
};

watch(
  () => [savedRepliesSearchQuery?.value, savedRepliesListResource.data],
  ([query, data]) => {
    if (!query) {
      savedRepliesList.value = data || [];
      return;
    }
    savedRepliesList.value =
      data?.filter((item) => {
        return item.name.toLowerCase().includes(query.toLowerCase());
      }) || [];
  }
);
</script>
