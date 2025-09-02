<template>
  <div class="w-full">
    <div class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base">
      <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
        <Avatar
          :image="activity?._caller?.image"
          :label="activity?._caller?.label"
          size="md"
        />
        <span class="font-medium text-ink-gray-8 ml-1">
          {{ activity?._caller?.label }}
        </span>
        <span>{{
          activity.call_type == "Incoming"
            ? __("has reached out")
            : __("has made a call")
        }}</span>
      </div>
      <div class="ml-auto whitespace-nowrap">
        <Tooltip :text="dateFormat(activity.creation, 'MMM D, dddd')">
          <div class="text-sm text-ink-gray-5">
            {{ __(timeAgo(activity.creation)) }}
          </div>
        </Tooltip>
      </div>
    </div>
    <div
      @click="showCallLogDetailModal = true"
      class="flex flex-col gap-2 cursor-pointer border-transparent shadow rounded-md bg-surface-cards px-3 py-2.5 text-ink-gray-9"
    >
      <div class="flex items-center justify-between">
        <div class="inline-flex gap-2 items-center text-base font-medium">
          <div>
            {{
              activity.call_type == "Incoming"
                ? __("Inbound Call")
                : __("Outbound Call")
            }}
          </div>
        </div>
        <div>
          <MultipleAvatar
            :avatars="[
              {
                name: activity._caller.label,
                label: activity._caller.label,
                image: activity._caller.image,
              },
              {
                name: activity._receiver.label,
                label: activity._receiver.label,
                image: activity._receiver.image,
              },
            ]"
            size="sm"
          />
        </div>
      </div>
      <div class="flex items-center flex-wrap gap-2">
        <Badge :label="dateFormat(activity.creation, 'MMM D, dddd')">
          <template #prefix>
            <CalendarIcon class="size-3" />
          </template>
        </Badge>
        <Badge v-if="activity.status == 'Completed'" :label="activity.duration">
          <template #prefix>
            <DurationIcon class="size-3" />
          </template>
        </Badge>
        <Badge
          v-if="activity.recording_url"
          :label="__('Listen')"
          class="cursor-pointer"
        >
          <template #prefix>
            <PlayIcon class="size-3" />
          </template>
        </Badge>
        <Badge
          :label="statusLabelMap[activity.status]"
          :theme="statusColorMap[activity.status]"
        />
      </div>
    </div>
    <CallLogDetailModal
      v-model="showCallLogDetailModal"
      v-model:callLogModal="showCallLogModal"
      :callLogId="props.activity.name"
      :hideTicket="true"
    />
    <CallLogModal
      v-model="showCallLogModal"
      :callLogId="props.activity.name"
      @afterInsert="refreshTicket()"
    />
  </div>
</template>
<script setup lang="ts">
import { dateFormat, timeAgo } from "@/utils";
import { Avatar, Badge, Tooltip } from "frappe-ui";
import { inject, ref } from "vue";
import MultipleAvatar from "./MultipleAvatar.vue";
import CalendarIcon from "./icons/CalendarIcon.vue";
import DurationIcon from "./icons/DurationIcon.vue";
import PlayIcon from "./icons/PlayIcon.vue";
import { statusColorMap, statusLabelMap } from "@/pages/call-logs/utils";
import CallLogDetailModal from "@/pages/call-logs/CallLogDetailModal.vue";
import CallLogModal from "@/pages/call-logs/CallLogModal.vue";

const props = defineProps({
  activity: Object,
});

const showCallLogDetailModal = ref(false);
const showCallLogModal = ref(false);

const refreshTicket = inject<() => void>("refreshTicket");
</script>
