<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="-ml-0.5" />
      </template>
      <template #right-header>
        <Button
          label="Create"
          theme="gray"
          variant="solid"
          @click="
            () => {
              title = null;
              message = null;
              showNewDialog = true;
            }
          "
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-y-auto">
      <div
        v-if="cannedResponses.data?.length > 0"
        class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 p-4"
      >
        <div
          v-for="cannedResponse in cannedResponses.data"
          :key="cannedResponse.name"
          class="group flex h-60 cursor-pointer flex-col justify-between gap-2 rounded-lg border px-4 py-3 pt-2 shadow-sm hover:bg-gray-50"
          @click="editItem(cannedResponse)"
        >
          <div class="flex items-center justify-between">
            <div class="truncate text-lg font-medium">
              {{ cannedResponse.title }}
            </div>
            <Dropdown
              :options="[
                {
                  label: 'Delete',
                  icon: 'trash-2',
                  onClick: () => deleteItem(cannedResponse.name),
                },
              ]"
              @click.stop
            >
              <Button
                icon="more-horizontal"
                variant="ghosted"
                class="hover:bg-white"
              />
            </Dropdown>
          </div>
          <TextEditor
            v-if="cannedResponse.message"
            :content="cannedResponse.message"
            :editable="false"
            editor-class="prose-sm"
            class="flex-1 overflow-hidden response-preview"
          />
          <div class="mt-2 flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <UserAvatar :name="cannedResponse.owner" size="xs" />
              <div class="text-sm text-gray-800">
                {{ getUser(cannedResponse.owner).full_name }}
              </div>
            </div>
            <Tooltip
              :text="dateFormat(cannedResponse.modified, dateTooltipFormat)"
            >
              <div class="text-sm text-gray-700">
                {{ dayjs.tz(cannedResponse.modified).fromNow() }}
              </div>
            </Tooltip>
          </div>
        </div>
      </div>
      <EmptyState
        v-else
        title="No Canned Responses Found"
        @emptyStateAction="showNewDialog = true"
      />
    </div>
    <CannedResponseModal
      v-model="showNewDialog"
      v-model:title="title"
      v-model:message="message"
      :name="name"
      :is-new="name ? false : true"
      @close="
        () => {
          showNewDialog = false;
          title = null;
          message = null;
          name = null;
        }
      "
      @update="
        () => {
          cannedResponses.reload();
          showNewDialog = false;
          title = null;
          message = null;
          name = null;
        }
      "
    />
  </div>
</template>
<script setup lang="ts">
import { LayoutHeader } from "@/components";
import { CannedResponseModal } from "@/components/canned-response/";
import { dayjs } from "@/dayjs";
import { useUserStore } from "@/stores/user";
import { dateFormat, dateTooltipFormat } from "@/utils";
import {
  Breadcrumbs,
  Dropdown,
  TextEditor,
  Tooltip,
  call,
  createListResource,
  usePageMeta,
} from "frappe-ui";
import { ref } from "vue";
import { useRoute } from "vue-router";
import EmptyState from "../components/EmptyState.vue";

const { getUser } = useUserStore();

const breadcrumbs = [
  { label: "Canned Responses", route: { name: "CannedResponses" } },
];
const route = useRoute();

const title = ref(null);
const message = ref(null);
const name = ref(null);
const isNew = route.hash.split("#")[1] === "new";
const showNewDialog = ref(isNew || false);

const cannedResponses = createListResource({
  doctype: "HD Canned Response",
  fields: ["name", "title", "message", "owner", "modified"],
  auto: true,
  orderBy: "modified desc",
});

function editItem(cannedResponse) {
  title.value = cannedResponse.title;
  message.value = cannedResponse.message;
  name.value = cannedResponse.name;
  showNewDialog.value = true;
}

async function deleteItem(name) {
  await call("frappe.client.delete", {
    doctype: "HD Canned Response",
    name,
  });
  cannedResponses.reload();
}

usePageMeta(() => {
  return {
    title: "Canned Responses",
  };
});
</script>

<style>
.response-preview :where(p, span, a) {
  @apply !text-gray-600;
}
</style>
