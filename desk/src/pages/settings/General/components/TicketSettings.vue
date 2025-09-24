<template>
  <div>
    <div class="text-lg font-semibold text-gray-900">Ticket settings</div>
    <div
      v-if="ticketTypeList.data && ticketStatusList.data && settingsData.doc"
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
                  //   settingsData.doc.default_ticket_type = option.value;
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
                class="w-full"
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
          <span class="text-p-sm text-ink-gray-6"
            >The ticket status will automatically change to “Replied” whenever
            the agent respond to a ticket.</span
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
                  ticketStatusList.data?.find(
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
                v-for="option in ticketStatusList.data"
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
                class="w-full"
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, createListResource, Popover, Switch } from "frappe-ui";
import { inject } from "vue";

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

const ticketStatusList = createListResource({
  doctype: "HD Ticket Status",
  name: "HD Ticket Status",
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

const settingsData = inject<any>("settingsData");

const onChange = (data) => {
  settingsData.setValue.submit(data);
};
</script>
