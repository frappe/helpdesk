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
          @change="getResponsePreview"
        />

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
import {
  createListResource,
  createResource,
  Dialog,
  FormLabel,
  TextEditor,
  toast,
} from "frappe-ui";
import { LoadingIndicator } from "frappe-ui";
import { menuButtons } from "../cannedResponse";
import { Link } from "@/components";
import { watch } from "vue";
import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";

const dialogModel = defineModel<{
  show: boolean;
  ticketId: string;
  cannedResponse: string;
  preview: string;
}>();

const { userTeams } = storeToRefs(useAuthStore());

const getResponsePreviewResource = createResource({
  url: "helpdesk.api.canned_response.get_rendered_canned_response",
  onSuccess: (data) => {
    dialogModel.value.preview = data;
  },
});

const getResponsePreview = (ticketId: string) => {
  if (!ticketId) return;
  dialogModel.value.ticketId = ticketId;
  dialogModel.value.preview = null;
  getResponsePreviewResource.submit({
    ticket_id: ticketId,
    canned_response: dialogModel.value.cannedResponse,
  });
};

watch(
  () => dialogModel.value.show,
  (newShowValue) => {
    if (newShowValue) {
      createListResource({
        doctype: "HD Ticket",
        fields: ["name"],
        start: 0,
        pageLength: 1,
        auto: true,
        onSuccess: (data) => {
          if (data.length === 0) {
            toast.error(__("No tickets found to preview."));
            return;
          }
          dialogModel.value.ticketId = data[0].name;
          getResponsePreview(data[0].name);
        },
      });
    }
  }
);
</script>
