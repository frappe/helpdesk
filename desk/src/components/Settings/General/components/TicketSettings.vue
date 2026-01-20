<template>
  <div>
    <div class="text-base font-semibold text-gray-900">
      {{ __("Ticket settings") }}
    </div>
    <div class="mt-6 flex flex-col gap-6">
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Make feedback mandatory")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __(
              "The feedback dialog will be shown, when a user tries to close a ticket from the customer portal."
            )
          }}</span>
        </div>
        <Switch v-model="settingsData.isFeedbackMandatory" />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Enable comment reactions")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __("Allow users to react to comments with emojis")
          }}</span>
        </div>
        <Switch v-model="settingsData.enableCommentReactions" />
      </div>
      <div>
        <div class="flex items-center justify-between">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">{{
              __("Restrict tickets by team")
            }}</span>
            <span class="text-p-sm text-ink-gray-6">{{
              __(
                "Restrict tickets to be viewed and managed by team members only."
              )
            }}</span>
          </div>
          <Switch v-model="settingsData.restrictTicketsByAgentGroup" />
        </div>
        <div
          class="grid grid-cols-2 gap-4 mt-3"
          v-if="settingsData.restrictTicketsByAgentGroup"
        >
          <Checkbox
            size="sm"
            v-model="settingsData.doNotRestrictTicketsWithoutAnAgentGroup"
            :label="__('Do not restrict tickets without a team')"
          />
          <Checkbox
            size="sm"
            v-model="settingsData.assignWithinTeam"
            :label="__('Restrict agent assignment to selected team')"
          />
        </div>
      </div>
      <div
        class="flex items-center justify-between"
        v-if="settingsData.restrictTicketsByAgentGroup"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Disable global saved replies")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __(
              "Agents will no longer be able to view and create saved replies with global scope."
            )
          }}</span>
        </div>
        <Switch v-model="settingsData.disableSavedRepliesGlobalScope" />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Auto update status")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __(
              "The ticket status will automatically change whenever the agent respond to a ticket."
            )
          }}</span>
        </div>
        <SelectDropdown
          :options="autoUpdateTicketStatusList"
          :model-value="settingsData.updateStatusTo"
          @update:model-value="
            (value) => {
              if (value) {
                settingsData.updateStatusTo = value;
                settingsData.autoUpdateStatus = true;
              } else {
                settingsData.updateStatusTo = null;
                settingsData.autoUpdateStatus = false;
              }
            }
          "
          target-class="max-w-40"
          placement="bottom-start"
        />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Allow anyone to create tickets")
          }}</span>
          <span class="text-p-sm text-ink-gray-6"
            >{{
              __(
                "Anyone will be able to create tickets without any permission. e.g. from webform."
              )
            }}
          </span>
        </div>
        <Switch
          :model-value="settingsData.allowAnyoneToCreateTickets"
          @update:model-value="
            (value) => (settingsData.allowAnyoneToCreateTickets = value)
          "
        />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Default ticket type")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __("Select what type all tickets get by default.")
          }}</span>
        </div>
        <SelectDropdown
          :options="ticketTypeList.data"
          v-model="settingsData.defaultTicketType"
          target-class="max-w-40"
          placement="bottom-start"
        />
      </div>
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Automatically close stale tickets")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __(
              "Auto-close tickets that remain in a status for the specified number of days."
            )
          }}</span>
        </div>
        <div class="grid grid-cols-2 gap-4 mt-3">
          <div class="flex flex-col gap-1.5">
            <FormLabel :label="__('Ticket status')" />
            <SelectDropdown
              :options="autoCloseTicketStatusList"
              :model-value="settingsData.autoCloseStatus"
              @update:model-value="
                (value) => {
                  if (value) {
                    settingsData.autoCloseStatus = value;
                    settingsData.autoCloseTickets = true;
                  } else {
                    settingsData.autoCloseStatus = null;
                    settingsData.autoCloseTickets = false;
                  }
                }
              "
              target-class="w-full"
              placement="bottom-start"
            />
          </div>
          <div class="flex flex-col gap-1.5">
            <FormControl
              :label="__('Auto-close after (Days)')"
              placeholder="e.g. 30"
              v-model="settingsData.autoCloseAfterDays"
              type="number"
              :debounce="300"
              :disabled="!settingsData.autoCloseStatus"
            />
            <ErrorMessage
              :message="
                settingsData.autoCloseStatus &&
                settingsData.autoCloseAfterDays < 1
                  ? __('The number of days must be 1 or more')
                  : ''
              "
            />
          </div>
        </div>
      </div>
      <div class="flex flex-col gap-2">
        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <div class="flex flex-col gap-1">
              <span class="text-base font-medium text-ink-gray-8">{{
                __(
                  "Display a customizable banner when customers raise tickets outside working hours."
                )
              }}</span>
              <span class="text-p-sm text-ink-gray-6"
                >{{
                  __(
                    "Show a customizable message to customers when they raise tickets outside of working hours."
                  )
                }}
              </span>
            </div>
            <Switch v-model="settingsData.showOutsideWorkingHoursBanner" />
          </div>
          <Textarea
            v-if="settingsData.showOutsideWorkingHoursBanner"
            variant="subtle"
            size="sm"
            placeholder="Enter Notification Message"
            :required="true"
            v-model="settingsData.outsideWorkingHoursBannerMessage"
          />
        </div>
        <div
          v-if="settingsData.showOutsideWorkingHoursBanner"
          class="flex gap-x-1 items-start justify-between"
        >
          <p class="text-sm text-gray-700 leading-5">
            {{
              __(
                "Find out all of the variables that can be used in the content"
              )
            }}
            <a
              href="https://docs.frappe.io/helpdesk/#"
              target="_blank"
              class="underline font-semibold"
              >{{ __("here") }}</a
            >
          </p>
          <Button
            :disabled="!canResetBannerContent"
            type="button"
            size="sm"
            variant="subtle"
            @click="onResetBannerContent"
            class="w-fit"
          >
            {{ __("Reset Content") }}
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SelectDropdown from "@/components/SelectDropdown.vue";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { HDSettingsSymbol } from "@/types";
import { HDTicketStatus } from "@/types/doctypes";
import {
  Checkbox,
  createListResource,
  createResource,
  ErrorMessage,
  FormControl,
  FormLabel,
  Switch,
  Textarea,
} from "frappe-ui";
import { computed, inject } from "vue";

const settingsData = inject(HDSettingsSymbol);
const { statuses } = useTicketStatusStore();

const bannerMsgResource = createResource({
  url: "helpdesk.helpdesk.doctype.hd_settings.helpers.check_banner_msg",
  auto: true,
});

const defaultBannerMessage = computed(() => {
  return bannerMsgResource.data?.default || "";
});

const canResetBannerContent = computed(() => {
  if (!settingsData?.value || !defaultBannerMessage.value) {
    return false;
  }
  return (
    settingsData.value.outsideWorkingHoursBannerMessage !==
    defaultBannerMessage.value
  );
});

const onResetBannerContent = () => {
  if (settingsData?.value && defaultBannerMessage.value) {
    settingsData.value.outsideWorkingHoursBannerMessage =
      defaultBannerMessage.value;
  }
};

const ticketTypeList = createListResource({
  doctype: "HD Ticket Type",
  name: "HD Ticket Type",
  auto: true,
  transform: (data) => {
    return data.map((item) => {
      return {
        label: item.name,
        value: item.name,
      };
    });
  },
});

const autoUpdateTicketStatusList = computed(() => {
  return (
    statuses.data?.map((s: HDTicketStatus) => {
      return {
        label: s.label_agent,
        value: s.label_agent,
      };
    }) || []
  );
});

const autoCloseTicketStatusList = computed(() => {
  return (
    statuses.data
      ?.filter(
        (s: HDTicketStatus) =>
          s.category === "Resolved" || s.category === "Paused"
      )
      ?.map((s: HDTicketStatus) => {
        return {
          label: s.label_agent,
          value: s.label_agent,
        };
      }) || []
  );
});
</script>
