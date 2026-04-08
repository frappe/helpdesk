<template>
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
              class="text-sm text-ink-gray-8"
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

<script setup lang="ts">
import { useShortcut } from "@/composables/shortcuts";
import { ActivitiesSymbol, AssigneeSymbol, TicketSymbol } from "@/types";
import { Popover, toast } from "frappe-ui";
import { inject, useTemplateRef } from "vue";
import LucideChevronDown from "~icons/lucide/chevron-down";
import MultipleAvatar from "../MultipleAvatar.vue";
import AssignToBody from "./AssignToBody.vue";
const ticket = inject(TicketSymbol);
const assignees = inject(AssigneeSymbol);
const activities = inject(ActivitiesSymbol);
async function saveAssignees(
  addedAssignees,
  removedAssignees,
  addAssignees,
  removeAssignees
) {
  try {
    if (removedAssignees.length) {
      const removeResult = await removeAssignees.submit(removedAssignees);
      if (removeResult?.exc) throw new Error(removeResult.exc);
    }

    if (addedAssignees.length) {
      const addResult = await addAssignees.submit(addedAssignees);
      if (addResult?.exc) throw new Error(addResult.exc);
    }

    toast.success(__("Assignee's updated successfully."));
    activities.value.reload();
  } catch (error) {
    toast.error(__("Failed to update Assignee's."));
  }
}

const assignToRef = useTemplateRef("assigneeButton");

useShortcut("a", () => {
  (assignToRef.value?.$el as HTMLElement)?.nextElementSibling?.click();
});
</script>
