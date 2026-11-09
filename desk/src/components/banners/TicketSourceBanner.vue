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
      <div class="flex items-center gap-1.5 font-medium text-ink-gray-9">
        <LucideCircleCheck class="size-4 shrink-0" />
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
        <div class="flex items-center gap-1.5 font-medium text-ink-gray-9">
          <LucideWrench class="size-4 shrink-0" />
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
      <div
        class="overflow-hidden rounded-lg border border-outline-gray-2 text-p-sm"
      >
        <div
          class="flex items-baseline justify-between gap-2 border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-2"
        >
          <span class="font-medium text-ink-gray-9">
            {{ __("To update") }}
          </span>
          <span class="text-ink-gray-5">
            {{ __("{0} found", [scripts.length]) }}
          </span>
        </div>
        <ul class="p-1">
          <li v-for="script in scripts" :key="script.doctype + script.name">
            <a
              :href="deskLink(script)"
              target="_blank"
              class="grid grid-cols-[1fr_auto] items-center gap-x-2 rounded px-2 py-1.5 text-ink-gray-9 hover:bg-surface-gray-2 sm:grid-cols-[7rem_1fr_auto]"
            >
              <span class="col-span-2 text-sm text-ink-gray-5 sm:col-span-1">{{
                __(script.doctype)
              }}</span>
              <span class="min-w-0 break-words">{{ script.name }}</span>
              <LucideExternalLink class="size-3.5 text-ink-gray-4" />
            </a>
          </li>
        </ul>
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
import { copyToClipboard } from "@helpdesk/shared/utils";
import { computed } from "vue";
import LucideCircleCheck from "~icons/lucide/circle-check";
import LucideCopy from "~icons/lucide/copy";
import LucideExternalLink from "~icons/lucide/external-link";
import LucideTriangleAlert from "~icons/lucide/triangle-alert";
import LucideWrench from "~icons/lucide/wrench";
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
