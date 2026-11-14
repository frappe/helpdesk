<template>
  <section class="flex flex-col gap-3">
    <div v-if="templates.data" class="flex items-center gap-2">
      <TextInput
        v-if="templates.data?.length"
        v-model="search"
        class="min-w-0 flex-1"
        :placeholder="__('Search template')"
        :debounce="300"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-6" />
        </template>
      </TextInput>
      <!-- Meta owns approval, so a status only moves on a sync or a webhook -->
      <Button
        class="ms-auto shrink-0"
        :label="__('Sync')"
        icon-left="lucide-refresh-cw"
        :loading="syncing"
        @click="sync"
      />
    </div>
    <div
      v-if="!templates.data && !templates.list.error"
      class="flex items-center justify-center py-10 text-ink-gray-5"
    >
      <LoadingIndicator class="size-4" />
    </div>
    <Alert
      v-else-if="templates.list.error"
      theme="red"
      :title="__('Could not load templates')"
      :primary-action="{ label: __('Retry'), onClick: templates.reload }"
    />
    <div v-else-if="filtered.length" class="-mx-2 flex flex-col">
      <template v-for="(template, index) in filtered" :key="template.name">
        <hr v-if="index" class="mx-2 border-outline-elevation-2" />
        <div
          class="flex items-center gap-3 rounded-4 px-2 py-3 hover:bg-surface-gray-2"
          data-testid="whatsapp-template"
        >
          <button
            class="flex min-w-0 flex-1 flex-col items-start gap-1 text-start"
            @click="emit('open', template.name)"
          >
            <span class="max-w-full truncate text-base-medium text-ink-gray-8">
              {{ template.template_label || template.template_name }}
            </span>
            <span class="max-w-full truncate text-p-sm text-ink-gray-6">
              {{ details(template) }}
            </span>
          </button>
          <Badge
            variant="subtle"
            :theme="STATUS_THEME[template.status] || 'gray'"
            :label="__(template.status)"
          />
          <Dropdown
            align="end"
            :options="rowOptions(template)"
            @update:open="(open: boolean) => open && (confirmingDelete = false)"
          >
            <Button
              icon="lucide-more-horizontal"
              variant="ghost"
              :aria-label="__('Template actions')"
            />
          </Dropdown>
        </div>
      </template>
    </div>
    <p v-else-if="search" class="py-10 text-center text-p-sm text-ink-gray-6">
      {{ __("No templates match your search") }}
    </p>
    <div
      v-else
      class="flex flex-col items-center gap-3 rounded-6 border border-dashed border-outline-gray-2 px-4 py-10 text-center"
      data-testid="whatsapp-templates-empty"
    >
      <div
        class="grid size-10 place-items-center rounded-full bg-surface-gray-2 text-ink-gray-6"
      >
        <WhatsAppIcon class="size-5" aria-hidden="true" />
      </div>
      <div class="flex flex-col gap-1">
        <span class="text-base-medium text-ink-gray-8">
          {{ __("No WhatsApp templates yet") }}
        </span>
        <span class="max-w-72 text-p-sm text-ink-gray-6">
          {{
            __(
              "Create one, or sync the templates already on your Meta account."
            )
          }}
        </span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import WhatsAppIcon from "@/components/whatsapp/WhatsAppIcon.vue";
import { __ } from "@/translation";
import { ConfirmDelete } from "@helpdesk/shared/utils";
import {
  Alert,
  Badge,
  Button,
  call,
  createListResource,
  Dropdown,
  LoadingIndicator,
  TextInput,
  toast,
} from "frappe-ui";
import { computed, ref } from "vue";
import LucideSearch from "~icons/lucide/search";

interface Template {
  name: string;
  template_label: string | null;
  template_name: string;
  template_type: string | null;
  language: string | null;
  status: string;
  whatsapp_account: string | null;
}

const emit = defineEmits<{ open: [name: string] }>();

const TEMPLATE_API = "whatsapp.whatsapp.doctype.wa_template.wa_template";
const STATUS_THEME: Record<string, string> = {
  Pending: "orange",
  Approved: "green",
  Rejected: "red",
  Deleted: "gray",
};

const search = ref("");
const syncing = ref(false);
const confirmingDelete = ref(false);

const templates = createListResource({
  doctype: "WA Template",
  fields: [
    "name",
    "template_label",
    "template_name",
    "template_type",
    "language",
    "status",
    "whatsapp_account",
  ],
  orderBy: "creation desc",
  pageLength: 99,
  auto: true,
});

const filtered = computed<Template[]>(() => {
  const query = search.value.toLowerCase();
  const all: Template[] = templates.data ?? [];
  if (!query) return all;
  return all.filter((template) =>
    [template.template_label, template.template_name, template.language].some(
      (field) => field?.toLowerCase().includes(query)
    )
  );
});

function details(template: Template): string {
  return [template.template_type, template.language, template.whatsapp_account]
    .filter(Boolean)
    .join(" · ");
}

/** Syncs each active account on its own, since the app's sync_all stops to ask which one when there are several. */
async function sync() {
  syncing.value = true;
  try {
    const accounts: { name: string }[] = await call(
      `${TEMPLATE_API}.get_active_accounts`
    );
    if (!accounts?.length) {
      toast.error(__("No active WhatsApp account to sync from"));
      return;
    }
    reportSync(await syncEach(accounts));
    templates.reload();
  } catch (error) {
    toast.error((error as any)?.messages?.[0] || __("Sync failed"));
  } finally {
    syncing.value = false;
  }
}

// One at a time to stay under Meta's rate limit; one broken account must not stop the rest
async function syncEach(accounts: { name: string }[]) {
  const totals = { created: 0, updated: 0, synced: 0, failed: [] as string[] };
  for (const { name } of accounts) {
    try {
      const result = await call(`${TEMPLATE_API}.sync_from_account`, {
        account_name: name,
      });
      totals.created += result?.total_synced || 0;
      totals.updated += result?.total_skipped || 0;
      totals.synced += 1;
    } catch {
      totals.failed.push(name);
    }
  }
  return totals;
}

function reportSync(totals: Awaited<ReturnType<typeof syncEach>>) {
  if (totals.synced) {
    toast.success(__("{0} new, {1} updated", [totals.created, totals.updated]));
  }
  if (totals.failed.length) {
    toast.error(__("Could not sync {0}", [totals.failed.join(", ")]));
  }
}

function rowOptions(template: Template) {
  return [
    {
      label: __("Edit"),
      icon: "lucide-pencil",
      onClick: () => emit("open", template.name),
    },
    ...ConfirmDelete({
      isConfirmingDelete: confirmingDelete,
      onConfirmDelete: () => remove(template),
    }),
  ];
}

function remove(template: Template) {
  templates.delete.submit(template.name, {
    onSuccess: () => toast.success(__("Template deleted")),
    onError: (error: { messages?: string[] }) =>
      toast.error(error?.messages?.[0] || __("Could not delete the template")),
  });
}
</script>
