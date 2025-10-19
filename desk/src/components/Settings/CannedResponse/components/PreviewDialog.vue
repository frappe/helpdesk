<template>
  <Dialog
    v-model="dialogModel.show"
    :options="{ title: __('Preview'), size: '2xl' }"
    @after-leave="
      () => {
        dialogModel.ticketId = '';
        dialogModel.preview = null;
      }
    "
  >
    <template #body-content>
      <div class="space-y-4">
        <Link
          :value="dialogModel.ticketId"
          :label="__('Select ticket to preview')"
          doctype="HD Ticket"
          class="form-control flex-1"
          placeholder="Search ticket"
          :show-description="true"
          @change="getResponsePreview($event)"
        >
          <template #target="{ togglePopover }">
            <div class="w-full">
              <button
                class="flex w-full items-center justify-between focus:outline-none text-base rounded h-7 py-1.5 px-2 border border-gray-100 bg-gray-100 placeholder-gray-500 hover:border-gray-200 hover:bg-gray-200 focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400"
                @click="togglePopover()"
              >
                <div class="flex items-center">
                  <slot name="prefix" />
                  <span
                    class="overflow-hidden text-ellipsis whitespace-nowrap text-base leading-5"
                    v-if="dialogModel.ticketId"
                  >
                    {{ dialogModel.ticketId }}
                  </span>
                  <span class="text-base leading-5 text-gray-500" v-else>
                    {{ __("Select a ticket to preview") }}
                  </span>
                </div>
                <FeatherIcon
                  name="chevron-down"
                  class="h-4 w-4 text-gray-600"
                  aria-hidden="true"
                />
              </button>
            </div>
          </template>
        </Link>
        <div class="space-y-1.5">
          <FormLabel :label="__('Preview')" />
          <div class="relative">
            <TextEditor
              editor-class="!prose-sm max-w-full overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
              :bubble-menu="menuButtons"
              :content="dialogModel.preview"
              :editable="false"
            />
            <div
              v-if="getResponsePreviewResource.loading"
              class="absolute top-0 right-0 flex items-center justify-center size-full rounded-md bg-black/20"
            >
              <LoadingIndicator class="size-4" />
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { createResource, Dialog, FormLabel, TextEditor } from "frappe-ui";
import { LoadingIndicator } from "frappe-ui";
import { menuButtons } from "../cannedResponse";

const dialogModel = defineModel<{
  show: boolean;
  ticketId: string;
  cannedResponse: string;
  preview: string;
}>();

const getResponsePreviewResource = createResource({
  url: "helpdesk.api.canned_response.get_rendered_canned_response",
  onSuccess: (data) => {
    dialogModel.value.preview = data;
  },
});

const getResponsePreview = (ticketId: string) => {
  dialogModel.value.ticketId = ticketId;
  dialogModel.value.preview = null;
  getResponsePreviewResource.submit({
    ticket_id: ticketId,
    canned_response: dialogModel.value.cannedResponse,
  });
};
</script>
