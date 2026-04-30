<template>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-3 border-b">
      <div class="flex items-center gap-2">
        <span class="text-base font-medium text-ink-gray-9">
          {{ __("Time Logs") }}
        </span>
        <span
          v-if="totalHours"
          class="text-sm text-ink-gray-5"
        >
          ({{ totalHours }}h total)
        </span>
      </div>
      <Button
        variant="subtle"
        size="sm"
        :label="showForm ? __('Cancel') : __('Add Entry')"
        @click="toggleForm"
      >
        <template v-if="!showForm" #prefix>
          <FeatherIcon name="plus" class="size-3.5" />
        </template>
      </Button>
    </div>

    <!-- Add Form -->
    <div v-if="showForm" class="px-5 py-3 border-b bg-surface-gray-2">
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label class="block text-xs text-ink-gray-6 mb-1.5">{{ __("Date") }}</label>
          <input
            type="date"
            v-model="form.date"
            class="w-full rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-sm text-ink-gray-8"
          />
        </div>
        <div>
          <label class="block text-xs text-ink-gray-6 mb-1.5">{{ __("Hours") }}</label>
          <input
            type="number"
            step="0.25"
            min="0"
            v-model="form.hours"
            :placeholder="__('e.g. 1.5')"
            class="w-full rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-sm text-ink-gray-8"
          />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label class="block text-xs text-ink-gray-6 mb-1.5">{{ __("Start Time") }}</label>
          <input
            type="time"
            v-model="form.start_time"
            class="w-full rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-sm text-ink-gray-8"
          />
        </div>
        <div>
          <label class="block text-xs text-ink-gray-6 mb-1.5">{{ __("End Time") }}</label>
          <input
            type="time"
            v-model="form.end_time"
            class="w-full rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-sm text-ink-gray-8"
          />
        </div>
      </div>
      <div class="mb-3">
        <label class="block text-xs text-ink-gray-6 mb-1.5">{{ __("Note") }}</label>
        <input
          type="text"
          v-model="form.note"
          :placeholder="__('What did you work on?')"
          class="w-full rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-sm text-ink-gray-8"
        />
      </div>
      <Button
        variant="solid"
        size="sm"
        :label="__('Save')"
        :loading="saving"
        @click="handleAdd"
      />
    </div>

    <!-- Time Logs List -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="timeLogs.length === 0" class="flex items-center justify-center py-20">
        <p class="text-sm text-ink-gray-5">{{ __("No time logs yet") }}</p>
      </div>
      <div v-else>
        <!-- Table Header -->
        <div
          class="grid gap-2 px-5 py-2 text-xs font-medium text-ink-gray-5 border-b"
          :style="{ gridTemplateColumns: '90px 60px 1fr 28px' }"
        >
          <span>{{ __("Date") }}</span>
          <span class="text-right">{{ __("Hours") }}</span>
          <span>{{ __("Note") }}</span>
          <span></span>
        </div>
        <!-- Rows -->
        <div
          v-for="log in timeLogs"
          :key="log.name"
          class="grid gap-2 px-5 py-2.5 items-center border-b text-sm hover:bg-surface-gray-2"
          :style="{ gridTemplateColumns: '90px 60px 1fr 28px' }"
        >
          <span class="text-ink-gray-8">{{ formatDate(log.date) }}</span>
          <span class="text-right font-medium text-ink-gray-9">
            {{ log.hours || '-' }}
          </span>
          <div class="truncate text-ink-gray-6">
            <span v-if="log.note">{{ log.note }}</span>
            <span v-else-if="log.start_time && log.end_time" class="text-ink-gray-4">
              {{ log.start_time }} - {{ log.end_time }}
            </span>
          </div>
          <button
            class="text-ink-gray-4 hover:text-ink-gray-8 rounded p-0.5"
            @click="handleDelete(log.name)"
          >
            <FeatherIcon name="x" class="size-3.5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { TicketSymbol } from "@/types";
import { Button, call, toast } from "frappe-ui";
import { computed, inject, reactive, ref } from "vue";

const ticket = inject(TicketSymbol);

const showForm = ref(false);
const saving = ref(false);

const form = reactive({
  date: "",
  start_time: "",
  end_time: "",
  hours: "",
  note: "",
});

function toggleForm() {
  showForm.value = !showForm.value;
  if (showForm.value) {
    form.date = new Date().toISOString().split("T")[0];
    form.start_time = "";
    form.end_time = "";
    form.hours = "";
    form.note = "";
  }
}

const timeLogs = computed(() => {
  return (ticket.value?.doc?.time_logs || []).slice().sort(
    (a, b) => new Date(b.date || b.creation).getTime() - new Date(a.date || a.creation).getTime()
  );
});

const totalHours = computed(() => {
  return ticket.value?.doc?.total_hours || 0;
});

function formatDate(date: string) {
  if (!date) return "";
  const d = new Date(date);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

async function handleAdd() {
  if (!form.date) {
    toast.error(__("Date is required"));
    return;
  }
  const hours = form.hours ? parseFloat(form.hours) : 0;
  if (!form.start_time && !form.end_time && !hours) {
    toast.error(__("Enter hours or start/end times"));
    return;
  }
  saving.value = true;
  try {
    await call(
      "helpdesk.helpdesk.doctype.hd_ticket.api.add_time_log",
      {
        ticket_id: String(ticket.value.doc.name),
        date: form.date,
        start_time: form.start_time || undefined,
        end_time: form.end_time || undefined,
        hours: hours,
        note: form.note || undefined,
      }
    );
    ticket.value.reload();
    showForm.value = false;
    toast.success(__("Time log added"));
  } catch (e: any) {
    toast.error(e.messages?.[0] || __("Failed to add time log"));
  }
  saving.value = false;
}

async function handleDelete(rowName: string) {
  try {
    await call(
      "helpdesk.helpdesk.doctype.hd_ticket.api.delete_time_log",
      {
        ticket_id: String(ticket.value.doc.name),
        row_name: String(rowName),
      }
    );
    ticket.value.reload();
    toast.success(__("Time log removed"));
  } catch (e: any) {
    toast.error(e.messages?.[0] || __("Failed to remove time log"));
  }
}
</script>
