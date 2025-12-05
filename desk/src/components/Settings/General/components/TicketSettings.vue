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
  ErrorMessage,
  FormControl,
  FormLabel,
  Switch,
} from "frappe-ui";
import { computed, inject } from "vue";

const settingsData = inject(HDSettingsSymbol);

const { statuses } = useTicketStatusStore();

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
