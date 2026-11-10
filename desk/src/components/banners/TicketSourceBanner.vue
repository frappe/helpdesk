<template>
  <SidebarBanner
    banner="ticket_source"
    :title="__('Fieldname changed')"
    :description="__('Via Customer Portal field is now called Source')"
    :dialog-title="__('Via Customer Portal is now Source')"
    :is-sidebar-collapsed="isSidebarCollapsed"
  >
    <p>
      <span class="font-medium text-ink-gray-8">{{ __("What changed:") }}</span>
      {{
        __(
          "The Via Customer Portal field on tickets is now called Source. Instead of a checkbox, Source says whether a ticket came in by Email or through the Portal. Tickets that agents raise count as Portal, as before."
        )
      }}
    </p>
    <div class="flex flex-col gap-1">
      <div class="font-medium text-ink-gray-9">
        {{ __("Updated for you") }}
      </div>
      <p>
        {{
          __(
            "If your SLAs, assignment rules or saved views used Via Customer Portal, we have switched them to Source where we could. Every ticket has its Source filled in too."
          )
        }}
      </p>
    </div>
    <template v-if="scripts.length">
      <div class="flex flex-col gap-1">
        <div class="font-medium text-ink-gray-9">
          {{ __("Needs your update") }}
        </div>
        <p>
          {{
            __(
              "You only need to update your own customizations. These still use the old field:"
            )
          }}
        </p>
      </div>
      <div class="rounded-5 border border-outline-gray-2 px-1 text-sm">
        <div
          class="grid items-center gap-6 p-2"
          :style="{ gridTemplateColumns }"
        >
          <div
            v-for="column in COLUMNS"
            :key="column.key"
            class="ms-2 overflow-hidden text-ellipsis whitespace-nowrap text-ink-gray-5"
          >
            {{ column.label }}
          </div>
        </div>
        <hr />
        <template
          v-for="(script, index) in scripts"
          :key="script.doctype + script.name"
        >
          <div
            class="grid items-start gap-6 p-2"
            :style="{ gridTemplateColumns }"
          >
            <div class="ms-2 flex min-h-8 min-w-0 items-center break-words">
              {{ __(script.doctype) }}
            </div>
            <div class="ms-2 flex min-h-8 min-w-0 items-center break-words">
              {{ script.name }}
            </div>
            <div class="flex min-h-8 items-center justify-end">
              <Button
                variant="ghost"
                icon="lucide-external-link"
                :href="deskLink(script)"
                :label="__('Open {0}', [script.name])"
              />
            </div>
          </div>
          <hr v-if="index !== scripts.length - 1" />
        </template>
      </div>
      <p>{{ __("In each one, change the old field to Source:") }}</p>
      <dl
        class="grid grid-cols-[auto_1fr] items-baseline gap-x-3 gap-y-1.5 text-p-sm"
      >
        <template v-for="rule in RULES" :key="rule.language">
          <dt class="text-sm text-ink-gray-5">{{ rule.language }}</dt>
          <dd class="min-w-0 break-words text-ink-gray-8">
            <code
              class="whitespace-nowrap rounded bg-surface-gray-2 px-1 font-mono text-xs"
              >{{ rule.from }}</code
            >
            →
            <code
              class="whitespace-nowrap rounded bg-surface-gray-2 px-1 font-mono text-xs"
              >{{ rule.to }}</code
            >
          </dd>
        </template>
      </dl>
      <div class="flex flex-wrap items-center gap-2.5">
        <Button
          :label="__('Copy fix prompt')"
          :icon-left="LucideCopy"
          @click="copyFixPrompt"
        />
        <span class="text-sm text-ink-gray-5">
          {{ __("Paste it into a coding agent to fix these for you.") }}
        </span>
      </div>
      <div class="flex gap-1.5 text-p-sm font-medium text-ink-gray-8">
        <LucideTriangleAlert class="mt-0.5 size-4 shrink-0" />
        {{ __("These stay broken until you fix them.") }}
      </div>
    </template>
  </SidebarBanner>
</template>

<script setup lang="ts">
import { type BannerScript, useBanners } from "@/composables/useBanners";
import { __ } from "@/translation";
import { getGridTemplateColumnsForTable } from "@/utils";
import { copyToClipboard } from "@helpdesk/shared/utils";
import { computed } from "vue";
import LucideCopy from "~icons/lucide/copy";
import LucideTriangleAlert from "~icons/lucide/triangle-alert";
import SidebarBanner from "./SidebarBanner.vue";

defineProps<{ isSidebarCollapsed: boolean }>();

const RULES = [
  {
    language: "Python",
    from: "doc.via_customer_portal",
    to: 'doc.source == "Portal"',
  },
  {
    language: "JavaScript",
    from: "doc.via_customer_portal",
    to: 'doc.source === "Portal"',
  },
  { language: "SQL", from: "via_customer_portal = 1", to: "source = 'Portal'" },
];

const COLUMNS = [
  { key: "doctype", label: __("Type"), width: "9rem" },
  { key: "name", label: __("Name") },
];
const gridTemplateColumns = getGridTemplateColumnsForTable(COLUMNS);

const { banner } = useBanners();
const scripts = computed(() => banner("ticket_source")?.scripts ?? []);

function deskLink(script: BannerScript): string {
  const slug = script.doctype.toLowerCase().replaceAll(" ", "-");
  return `/app/${slug}/${encodeURIComponent(script.name)}`;
}

function copyFixPrompt() {
  copyToClipboard(fixPrompt(window.location.origin), __("Fix prompt copied"));
}

function fixPrompt(site: string): string {
  const list = scripts.value.map((s) => `- ${s.doctype}: ${s.name}`);
  return `On my Frappe Helpdesk site ${site}, the HD Ticket field via_customer_portal (a checkbox)
was replaced by \`source\`, a Select field with the options "Email" and "Portal".

These scripts and conditions still use the old field and need fixing:
${list.join("\n")}

Use frappectl (log in with \`frappectl auth login ${site} --oauth\`) to read each one.
Change every use of via_customer_portal to source:
- a true check (doc.via_customer_portal, == 1, \`= 1\` in SQL) becomes source == "Portal"
  (=== "Portal" in JavaScript)
- a false check (not doc.via_customer_portal, !doc.via_customer_portal, == 0) becomes source == "Email"

Show me the change for each one and wait for my OK before you save it.`;
}
</script>
