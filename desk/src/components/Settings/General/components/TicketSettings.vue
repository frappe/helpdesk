<template>
  <div>
    <div class="text-base font-semibold text-gray-900">Ticket Settings</div>
    <div
      v-if="
        ticketTypeList.data && autoUpdateticketStatusList && settingsData.doc
      "
      class="mt-6 flex flex-col gap-6"
    >
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Default ticket type</span
          >
          <span class="text-p-sm text-ink-gray-6"
            >Select what type all tickets get by default</span
          >
        </div>
        <Popover>
          <template #target="{ togglePopover }">
            <div
              class="flex items-center justify-between text-base rounded h-7 py-1.5 pl-2 pr-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark] cursor-default min-w-28"
              @click="togglePopover()"
            >
              <div>
                {{
                  ticketTypeList.data?.find(
                    (option) =>
                      option.value == settingsData.doc.default_ticket_type
                  )?.value || "Select"
                }}
              </div>
              <FeatherIcon name="chevron-down" class="size-4 ml-2" />
            </div>
          </template>
          <template #body="{ togglePopover }">
            <div
              class="p-1 text-ink-gray-6 top-1 absolute w-min bg-white shadow-2xl rounded min-w-28"
            >
              <div
                v-for="option in ticketTypeList.data"
                :key="option.value"
                class="p-2 cursor-pointer hover:bg-gray-50 text-base flex items-center justify-between rounded"
                @click="
                  onChange({ default_ticket_type: option.value });
                  togglePopover();
                "
              >
                {{ option.label }}
                <FeatherIcon
                  v-if="settingsData.doc.default_ticket_type == option.value"
                  name="check"
                  class="size-4 ml-2"
                />
              </div>
              <hr class="my-1" />
              <Button
                variant="ghost"
                label="Reset"
                icon-left="refresh-ccw"
                class="w-full focus-visible:ring-0"
                @click="onChange({ default_ticket_type: null })"
              />
            </div>
          </template>
        </Popover>
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Allow anyone to create tickets</span
          >
          <span class="text-p-sm text-ink-gray-6"
            >Anyone will able to create tickets</span
          >
        </div>
        <Switch
          :model-value="settingsData.doc.allow_anyone_to_create_tickets"
          @update:model-value="
            onChange({ allow_anyone_to_create_tickets: $event })
          "
        />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Make feedback mandatory</span
          >
          <span class="text-p-sm text-ink-gray-6"
            >The feedback dialog will be shown, when a user tries to close a
            ticket.</span
          >
        </div>
        <Switch
          :model-value="settingsData.doc.is_feedback_mandatory"
          @update:model-value="onChange({ is_feedback_mandatory: $event })"
        />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Auto update status</span
          >
          <span class="text-p-sm text-ink-gray-6">{{
            __(
              "The ticket status will automatically change whenever the agent respond to a ticket."
            )
          }}</span>
        </div>
        <Popover>
          <template #target="{ togglePopover }">
            <div
              class="flex items-center justify-between text-base rounded h-7 py-1.5 pl-2 pr-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark] cursor-default min-w-28"
              @click="togglePopover()"
            >
              <div>
                {{
                  autoUpdateticketStatusList?.find(
                    (option) =>
                      option.value == settingsData.doc.update_status_to
                  )?.label || "Select"
                }}
              </div>
              <FeatherIcon name="chevron-down" class="size-4 ml-2" />
            </div>
          </template>
          <template #body="{ togglePopover }">
            <div
              class="p-1 text-ink-gray-6 top-1 absolute min-w-28 bg-white shadow-2xl rounded"
            >
              <div
                v-for="option in autoUpdateticketStatusList"
                :key="option.value"
                class="p-2 cursor-pointer hover:bg-gray-50 text-base flex items-center justify-between rounded"
                @click="
                  settingsData.doc.update_status_to = option.value;
                  settingsData.doc.auto_update_status = true;
                  onChange({
                    update_status_to: option.value,
                    auto_update_status: true,
                  });
                  togglePopover();
                "
              >
                {{ option.label }}
                <FeatherIcon
                  v-if="settingsData.doc.update_status_to == option.value"
                  name="check"
                  class="size-4 ml-2"
                />
              </div>
              <hr class="my-1" />
              <Button
                variant="ghost"
                label="Reset"
                icon-left="refresh-ccw"
                class="w-full focus-visible:ring-0"
                @click="
                  settingsData.doc.update_status_to = null;
                  settingsData.doc.auto_update_status = false;
                  onChange({
                    update_status_to: null,
                    auto_update_status: false,
                  });
                "
              />
            </div>
          </template>
        </Popover>
      </div>
      <div>
        <div class="flex items-center justify-between">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8"
              >Restrict tickets by Team</span
            >
            <span class="text-p-sm text-ink-gray-6"
              >Restrict tickets to be created by team members only.</span
            >
          </div>
          <Switch
            :model-value="settingsData.doc.restrict_tickets_by_agent_group"
            @update:model-value="
              onChange({ restrict_tickets_by_agent_group: $event })
            "
          />
        </div>
        <div
          class="grid grid-cols-2 gap-4 mt-3"
          v-if="settingsData.doc.restrict_tickets_by_agent_group"
        >
          <div
            class="flex items-start sm:items-center gap-2"
            @click="
              onChange({
                do_not_restrict_tickets_without_an_agent_group:
                  !settingsData.doc
                    .do_not_restrict_tickets_without_an_agent_group,
              })
            "
          >
            <Checkbox
              :model-value="
                settingsData.doc.do_not_restrict_tickets_without_an_agent_group
              "
            />
            <FormLabel label="Do not restrict tickets without a Team" />
          </div>
          <div
            class="flex items-start sm:items-center gap-2"
            @click="
              onChange({
                assign_within_team: !settingsData.doc.assign_within_team,
              })
            "
          >
            <Checkbox :model-value="settingsData.doc.assign_within_team" />
            <FormLabel label="Restrict agent assignment to selected Team" />
          </div>
        </div>
      </div>
      <div>
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Automatically Close Tickets</span
          >
          <span class="text-p-sm text-ink-gray-6"
            >Automatically close tickets after a certain condition is met.</span
          >
        </div>
        <div class="grid grid-cols-2 gap-4 mt-3">
          <div class="flex flex-col gap-1.5">
            <FormLabel label="Auto-close status" />
            <Popover>
              <template #target="{ togglePopover }">
                <div
                  class="flex items-center justify-between text-base rounded h-7 py-1.5 pl-2 pr-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark] cursor-default min-w-28"
                  @click="togglePopover()"
                >
                  <div>
                    {{
                      autoCloseTicketStatusList?.find(
                        (option) =>
                          option.value == settingsData.doc.auto_close_status
                      )?.label || "Select status"
                    }}
                  </div>
                  <FeatherIcon name="chevron-down" class="size-4 ml-2" />
                </div>
              </template>
              <template #body="{ togglePopover }">
                <div
                  class="p-1 text-ink-gray-6 top-1 absolute min-w-28 bg-white shadow-2xl rounded"
                >
                  <div
                    v-for="option in autoCloseTicketStatusList"
                    :key="option.value"
                    class="p-2 cursor-pointer hover:bg-gray-50 text-base flex items-center justify-between rounded"
                    @click="
                      settingsData.doc.auto_close_status = option.value;
                      onChange({
                        auto_close_tickets: true,
                        auto_close_status: option.value,
                        auto_close_after_days:
                          settingsData.doc.auto_close_after_days || 1,
                      });
                      togglePopover();
                    "
                  >
                    {{ option.label }}
                    <FeatherIcon
                      v-if="settingsData.doc.auto_close_status == option.value"
                      name="check"
                      class="size-4 ml-2"
                    />
                  </div>
                  <hr class="my-1" />
                  <Button
                    variant="ghost"
                    label="Reset"
                    icon-left="refresh-ccw"
                    class="w-full focus-visible:ring-0"
                    @click="
                      settingsData.doc.auto_close_status = null;
                      onChange({
                        auto_close_tickets: false,
                        auto_close_status: null,
                      });
                      togglePopover();
                    "
                  />
                </div>
              </template>
            </Popover>
          </div>
          <FormControl
            label="Auto-close after (Days)"
            placeholder="e.g. 30"
            :model-value="settingsData.doc.auto_close_after_days"
            @update:model-value="
              onChange({
                auto_close_after_days: Number($event) <= 0 ? 1 : Number($event),
              })
            "
            type="number"
            :debounce="300"
            :disabled="!settingsData.doc.auto_close_status"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { HDTicketStatus } from "@/types/doctypes";
import {
  Button,
  Checkbox,
  createListResource,
  FormControl,
  FormLabel,
  Popover,
  Switch,
} from "frappe-ui";
import { computed, inject } from "vue";

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

const settingsData = inject<any>("settingsData");

const onChange = (data) => {
  settingsData.setValue.submit(data);
};
</script>
