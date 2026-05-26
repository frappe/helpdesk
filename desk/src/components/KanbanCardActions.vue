<template>
  <div
    class="flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity"
  >
    <Popover placement="bottom-end">
      <template #target="{ togglePopover }">
        <Button
          icon="plus"
          variant="ghost"
          size="sm"
          class="!h-6 !w-6"
          @click.stop="togglePopover"
        />
      </template>
      <template #body="{ togglePopover }">
        <div
          class="min-w-[200px] rounded-lg bg-surface-modal shadow-lg ring-1 ring-black ring-opacity-5 overflow-hidden"
          @click.stop
        >
          <!-- Mode toggle -->
          <div v-if="!mode" class="flex flex-col py-1">
            <button
              class="flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-surface-gray-1 text-ink-gray-9"
              @click="mode = 'comment'"
            >
              <FeatherIcon
                name="message-circle"
                class="h-4 w-4 text-ink-gray-6"
              />
              {{ __("Add Comment") }}
            </button>
            <button
              class="flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-surface-gray-1 text-ink-gray-9"
              @click="mode = 'reply'"
            >
              <FeatherIcon
                name="corner-up-left"
                class="h-4 w-4 text-ink-gray-6"
              />
              {{ __("Reply") }}
            </button>
          </div>

          <!-- Editor -->
          <div v-else class="flex flex-col gap-2 p-3 w-80">
            <div class="text-xs font-medium uppercase text-ink-gray-5">
              {{ mode === "reply" ? __("Reply") : __("Comment") }}
            </div>
            <textarea
              v-model="content"
              :placeholder="
                mode === 'reply' ? __('Type your reply…') : __('Add a comment…')
              "
              rows="4"
              class="w-full resize-none rounded-md border border-outline-gray-2 bg-surface-white p-2 text-sm text-ink-gray-9 focus:border-outline-gray-3 focus:outline-none"
              @keydown.ctrl.enter.prevent="submit(togglePopover)"
              @keydown.meta.enter.prevent="submit(togglePopover)"
            />
            <div class="flex items-center justify-between">
              <Button
                variant="ghost"
                size="sm"
                :label="__('Cancel')"
                @click="cancel"
              />
              <Button
                variant="solid"
                size="sm"
                :label="mode === 'reply' ? __('Send Reply') : __('Comment')"
                :loading="submitting"
                @click="submit(togglePopover)"
              />
            </div>
          </div>
        </div>
      </template>
    </Popover>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button, FeatherIcon, Popover, call, toast } from "frappe-ui";
import { __ } from "@/translation";
import { reloadTicket } from "@/composables/useTicket";

const props = defineProps<{
  ticket: string;
}>();

const emit = defineEmits<{
  (e: "posted", mode: "comment" | "reply"): void;
}>();

const mode = ref<"comment" | "reply" | null>(null);
const content = ref("");
const submitting = ref(false);

function cancel() {
  mode.value = null;
  content.value = "";
}

async function submit(togglePopover: () => void) {
  const body = content.value.trim();
  if (!body) return;
  submitting.value = true;
  try {
    if (mode.value === "comment") {
      await call("frappe.client.insert", {
        doc: {
          doctype: "HD Ticket Comment",
          reference_ticket: props.ticket,
          content: body,
          commented_by: undefined, // server fills from session.user
        },
      });
    } else if (mode.value === "reply") {
      // Use Frappe's Communication doctype — same path used by the
      // existing reply UI on the ticket detail page.
      await call("frappe.client.insert", {
        doc: {
          doctype: "Communication",
          reference_doctype: "HD Ticket",
          reference_name: props.ticket,
          communication_medium: "Email",
          communication_type: "Communication",
          sent_or_received: "Sent",
          content: body,
          subject: "Re: " + props.ticket,
        },
      });
    }
    // Invalidate the cached ticket resource so the new comment/reply
    // shows up immediately when the user opens the ticket detail page
    // (without this, useTicket() returns the stale cached activities
    // and the user has to reload manually).
    reloadTicket(props.ticket);
    toast.success(
      mode.value === "reply" ? __("Reply sent") : __("Comment added")
    );
    emit("posted", mode.value as "comment" | "reply");
    mode.value = null;
    content.value = "";
    togglePopover();
  } catch (err: any) {
    toast.error(err?.message || __("Could not save"));
  } finally {
    submitting.value = false;
  }
}
</script>
