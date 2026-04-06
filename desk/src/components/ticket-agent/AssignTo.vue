<template>
  <template v-if="canAssign">
  <Popover class="flex w-full" placement="bottom-end">
    <template #target="{ open, close, togglePopover }">
      <div class="flex flex-col gap-1.5 w-full">
        <span class="block text-xs text-gray-600">Assignee</span>
        <Button
          variant="outline"
          class="!flex !justify-start w-full active:!bg-inherit hover:shadow-sm"
          ref="assigneeButton"
          @click="togglePopover()"
        >
          <p v-if="assignees.loading || assignees.data?.length === 0">
            {{ __("No assignees") }}
          </p>
          <div
            v-else-if="assignees.data?.length >= 1"
            class="flex gap-1.5 items-center"
          >
            <MultipleAvatar
              :avatars="assignees.data.map((a) => a.name)"
              size="sm"
            />
            <p
              v-if="assignees.data?.length > 1"
              class="ml-2 text-sm text-ink-gray-8"
            >
              {{ assignees.data?.length }} assignees
            </p>
          </div>
          <template #suffix>
            <Icon
              :icon="LucideChevronDown"
              class="h-4 w-4 ml-auto text-ink-gray-5"
            />
          </template>
        </Button>
      </div>
    </template>
    <template #body="{ isOpen }">
      <AssignToBody
        v-show="isOpen"
        v-model="assignees.data"
        doctype="HD Ticket"
        :docname="ticket.name"
        :open="isOpen"
        :onUpdate="saveAssignees"
      />
    </template>
  </Popover>
  </template>
  <template v-else>
    <div class="flex flex-col gap-1.5 w-full">
      <span class="block text-xs text-gray-600">{{ __("Assignee") }}</span>
      <div class="text-sm text-ink-gray-6 py-1 px-1">
        <span v-if="assignees.data?.length">
          {{ assignees.data.map((a) => a.name).join(", ") }}
        </span>
        <span v-else class="text-ink-gray-4">{{ __("No assignees") }}</span>
      </div>
    </div>
  </template>
</template>

<script setup lang="ts">
import { useShortcut } from "@/composables/shortcuts";
import { ActivitiesSymbol, AssigneeSymbol, TicketSymbol } from "@/types";
import { Popover } from "frappe-ui";
import { computed, inject, useTemplateRef } from "vue";
import { createResource } from "frappe-ui";
import LucideChevronDown from "~icons/lucide/chevron-down";
import MultipleAvatar from "../MultipleAvatar.vue";
import AssignToBody from "./AssignToBody.vue";
const ticket = inject(TicketSymbol);
const assignees = inject(AssigneeSymbol);
const activities = inject(ActivitiesSymbol);

const assignPermission = createResource({
  url: "helpdesk.api.doc.can_assign_ticket",
  auto: true,
});

const canAssign = computed(() => assignPermission.data === true);
async function saveAssignees(
  addedAssignees,
  removedAssignees,
  addAssignees,
  removeAssignees
) {
  removedAssignees.length && (await removeAssignees.submit(removedAssignees));
  addedAssignees.length && (await addAssignees.submit(addedAssignees));
  activities.value.reload();
}

const assignToRef = useTemplateRef("assigneeButton");

useShortcut("a", () => {
  (assignToRef.value?.$el as HTMLElement)?.nextElementSibling?.click();
});
</script>
