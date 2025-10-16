<template>
  <div>
    <div class="text-base font-semibold text-gray-900">
      {{ __("Ticket Settings") }}
    </div>
    <div class="mt-6 flex flex-col gap-6">
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Make feedback mandatory")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __(
              "The feedback dialog will be shown, when a user tries to close a ticket from the customer portal"
            )
          }}</span>
        </div>
        <Switch v-model="settingsData.isFeedbackMandatory" />
      </div>
      <div>
        <div class="flex items-center justify-between">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">{{
              __("Restrict tickets by Team")
            }}</span>
            <span class="text-p-sm text-ink-gray-6">{{
              __("Restrict tickets to be created by team members only.")
            }}</span>
          </div>
          <Switch v-model="settingsData.restrictTicketsByAgentGroup" />
        </div>
        <div
          class="grid grid-cols-2 gap-4 mt-3"
          v-if="settingsData.restrictTicketsByAgentGroup"
        >
          <div
            class="flex items-start sm:items-center gap-2"
            @click="
              () => {
                settingsData.doNotRestrictTicketsWithoutAnAgentGroup =
                  !settingsData.doNotRestrictTicketsWithoutAnAgentGroup;
              }
            "
          >
            <Checkbox
              :model-value="
                settingsData.doNotRestrictTicketsWithoutAnAgentGroup
              "
            />
            <FormLabel :label="__('Do not restrict tickets without a Team')" />
          </div>
          <div
            class="flex items-start sm:items-center gap-2"
            @click="
              () => {
                settingsData.assignWithinTeam = !settingsData.assignWithinTeam;
              }
            "
          >
            <Checkbox :model-value="settingsData.assignWithinTeam" />
            <FormLabel
              :label="__('Restrict agent assignment to selected Team')"
            />
          </div>
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
          :options="autoUpdateticketStatusList"
          :model-value="settingsData.updateStatusTo"
          target-class="max-w-40"
          placement="bottom-end"
          @on-reset="
            () => {
              settingsData.updateStatusTo = null;
              settingsData.autoUpdateStatus = false;
            }
          "
          @on-change="
            (value) => {
              settingsData.updateStatusTo = value;
              settingsData.autoUpdateStatus = true;
            }
          "
        />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Allow anyone to create tickets")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __("Anyone will able to create tickets, e.g. from webform")
          }}</span>
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
            __("Select what type all tickets get by default")
          }}</span>
        </div>
        <SelectDropdown
          :options="ticketTypeList.data"
          :model-value="settingsData.defaultTicketType"
          target-class="max-w-40"
          placement="bottom-end"
          @on-reset="() => (settingsData.defaultTicketType = null)"
          @on-change="(value) => (settingsData.defaultTicketType = value)"
        />
      </div>
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Automatically Close Tickets")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __("Automatically close tickets after a certain condition is met.")
          }}</span>
        </div>
        <div class="grid grid-cols-2 gap-4 mt-3">
          <div class="flex flex-col gap-1.5">
            <FormLabel :label="__('Auto-close status')" />
            <SelectDropdown
              :options="autoCloseTicketStatusList"
              :model-value="settingsData.autoCloseStatus"
              target-class="w-full"
              placement="bottom-end"
              @on-reset="
                () => {
                  settingsData.autoCloseStatus = null;
                  settingsData.autoCloseTickets = false;
                }
              "
              @on-change="
                (value) => {
                  settingsData.autoCloseStatus = value;
                  settingsData.autoCloseTickets = true;
                }
              "
            />
          </div>
          <div class="flex flex-col gap-1.5">
            <FormControl
              :label="__('Auto-close after (Days)')"
              placeholder="e.g. 30"
              :model-value="settingsData.autoCloseAfterDays"
              @update:model-value="
                (value) => (settingsData.autoCloseAfterDays = value)
              "
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

const settingsData = inject<any>("settingsData");

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

const autoUpdateticketStatusList = computed(() => {
  return (
    statuses.data
      ?.filter(
        (s: HDTicketStatus) => s.category === "Open" || s.category === "Paused"
      )
      .map((s: HDTicketStatus) => {
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
      .map((s: HDTicketStatus) => {
        return {
          label: s.label_agent,
          value: s.label_agent,
        };
      }) || []
  );
});
</script>
