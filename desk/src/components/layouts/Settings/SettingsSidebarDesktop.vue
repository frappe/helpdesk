<template>
  <div
    class="flex select-none flex-col border-r border-gray-200 bg-gray-50 p-2 pt-3 text-base duration-300 ease-in-out overflow-clip max-w-[220px] min-w-[220px]"
  >
    <div class="mb-5 flex items-center gap-2">
      <Button
        icon="arrow-left"
        @click="() => router.push({ name: 'TicketsAgent' })"
        variant="ghost"
        class="ml-0.5"
      />
      <div class="text-base text-ink-gray-8">Settings</div>
    </div>
    <div v-for="(section, key) in links">
      <div class="text-base text-ink-gray-5">
        <span class="w-full overflow-clip text-nowrap">{{
          section.label
        }}</span>
      </div>
      <div class="flex flex-col gap-1 mt-2.5">
        <div v-for="item in section.items">
          <SidebarLink
            class="relative min-h-7"
            :label="item.label"
            :icon="item.icon"
            :to="item.to"
            :is-active="isActiveTab(item.to)"
            :is-expanded="true"
          >
            <template #label>
              <div
                class="-all ml-2 flex shrink-0 grow items-center justify-between text-base duration-300 ease-in-out opacity-100"
              >
                {{ item.label }}
              </div>
            </template>
          </SidebarLink>
        </div>
      </div>
      <hr v-if="key < links.length - 1" class="my-4" />
    </div>
  </div>
</template>
<script setup lang="ts">
import { SidebarLink } from "@/components";
import { useRoute, useRouter } from "vue-router";

import LucideMail from "~icons/lucide/mail";
import MailOpen from "~icons/lucide/mail-open";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucideUser from "~icons/lucide/user";
import ShieldCheck from "~icons/lucide/shield-check";
import Briefcase from "~icons/lucide/briefcase";
import Settings from "~icons/lucide/settings-2";
import SettingsGear from "~icons/lucide/settings";
import LucideUsers from "~icons/lucide/users";

import { Avatar, Button } from "frappe-ui";
import { FieldDependencyIcon, PhoneIcon } from "@/components/icons";
import { computed, h } from "vue";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

function isActiveTab(to: any) {
  if (route.query.view) {
    return route.query.view == to?.query?.view;
  }
  return route.name === to;
}

const links = computed(() =>
  [
    {
      label: "User Settings",
      show: true,
      items: [
        {
          label: "Profile",
          icon: h(Avatar, {
            image: auth.userImage,
            label: auth.userName,
            size: "xs",
          }),
          to: "Profile",
          isActive: isActiveTab("Profile"),
        },
      ],
    },
    {
      label: "Email Settings",
      show: auth.isManager,
      items: [
        {
          label: "Email Accounts",
          icon: LucideMail,
          to: "EmailAccounts",
          isActive: isActiveTab("EmailAccounts"),
        },
        {
          label: "Email Notifications",
          icon: MailOpen,
          to: "EmailNotificationsSettings",
          isActive: isActiveTab("EmailNotificationsSettings"),
        },
      ],
    },
    {
      label: "App Settings",
      show: auth.isManager,
      items: [
        {
          label: "General",
          icon: SettingsGear,
          to: "GeneralSettings",
          isActive: isActiveTab("GeneralSettings"),
        },
        {
          label: "Agents",
          icon: LucideUser,
          to: "Agents",
          isActive: isActiveTab("Agents"),
        },
        {
          label: "Invite Agent",
          icon: LucideUserPlus,
          to: "InviteAgent",
          isActive: isActiveTab("InviteAgent"),
        },
        {
          label: "Teams",
          icon: LucideUsers,
          to: "SettingsTeams",
          isActive: isActiveTab("SettingsTeams"),
        },
        {
          label: "SLA Policies",
          icon: ShieldCheck,
          to: "SLAPolicies",
          isActive: isActiveTab("SLAPolicies"),
        },
        {
          label: "Business Holidays",
          icon: Briefcase,
          to: "BusinessHolidays",
          isActive: isActiveTab("BusinessHolidays"),
        },
        {
          label: "Assignment Rules",
          icon: h(Settings, { class: "rotate-90" }),
          to: "AssignmentRules",
          isActive: isActiveTab("AssignmentRules"),
        },
        {
          label: "Field Dependencies",
          icon: FieldDependencyIcon,
          to: "FieldDependencies",
          isActive: isActiveTab("FieldDependencies"),
        },
      ],
    },
    {
      label: "Integrations",
      show: true,
      items: [
        {
          label: "Telephony Settings",
          icon: PhoneIcon,
          to: "TelephonySettings",
          isActive: isActiveTab("TelephonySettings"),
        },
      ],
    },
  ].filter((link) => link.show)
);
</script>
