<template>
  <div
    class="flex select-none flex-col border-r border-gray-200 bg-gray-50 p-2 pt-3 text-base duration-300 ease-in-out overflow-clip"
    :style="{
      'min-width': width,
      'max-width': width,
    }"
  >
    <div class="mb-1.5">
      <Button
        v-if="isExpanded"
        label="Back"
        class="!justify-start hover:!bg-transparent active:!bg-transparent hover:opacity-80 active:opacity-70 !px-0"
        :icon-left="LucideChevronLeft"
        @click="() => router.push({ name: 'TicketsAgent' })"
        variant="ghost"
      />
      <Button
        v-else
        class="hover:!bg-transparent active:!bg-transparent hover:opacity-80 active:opacity-70 duration-0 !px-0"
        :icon="LucideChevronLeft"
        @click="() => router.push({ name: 'TicketsAgent' })"
        variant="ghost"
        :class="{
          'ml-0.5': !isExpanded,
        }"
      />
    </div>
    <div v-for="section in links">
      <div v-if="isExpanded" class="text-base text-ink-gray-5 my-2.5">
        <span class="w-full overflow-clip text-nowrap">{{
          section.label
        }}</span>
      </div>
      <div v-for="item in section.items">
        <SidebarLink
          v-if="item.show"
          class="relative my-0.5 min-h-7"
          :label="item.label"
          :icon="item.icon"
          :to="item.to"
          :is-active="isActiveTab(item.to)"
          :is-expanded="isExpanded"
        />
      </div>
    </div>
    <div class="grow" />
    <div class="flex flex-col gap-2">
      <SidebarLink
        :icon="isExpanded ? LucideArrowLeftFromLine : LucideArrowRightFromLine"
        :is-active="false"
        :is-expanded="isExpanded"
        :label="isExpanded ? 'Collapse' : 'Expand'"
        :on-click="() => (isExpanded = !isExpanded)"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { SidebarLink } from "@/components";
import { useSidebarStore } from "@/stores/sidebar";
import { isCustomerPortal } from "@/utils";
import { storeToRefs } from "pinia";
import { useRoute, useRouter } from "vue-router";

import LucideArrowLeftFromLine from "~icons/lucide/arrow-left-from-line";
import LucideArrowRightFromLine from "~icons/lucide/arrow-right-from-line";
import LucideMail from "~icons/lucide/mail";
import MailOpen from "~icons/lucide/mail-open";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucideUser from "~icons/lucide/user";
import LucideChevronLeft from "~icons/lucide/chevron-left";
import ShieldCheck from "~icons/lucide/shield-check";
import Briefcase from "~icons/lucide/briefcase";
import Settings from "~icons/lucide/settings-2";
import SettingsGear from "~icons/lucide/settings";
import LucideUsers from "~icons/lucide/users";

import { Button } from "frappe-ui";
import { FieldDependencyIcon, PhoneIcon } from "@/components/icons";
import { h } from "vue";

const { isExpanded, width } = storeToRefs(useSidebarStore());
const route = useRoute();
const router = useRouter();

function isActiveTab(to: any) {
  if (route.query.view) {
    return route.query.view == to?.query?.view;
  }
  return route.name === to;
}

const links = [
  {
    label: "User Settings",
    show: true,
    items: [
      {
        label: "Profile",
        icon: LucideUser,
        to: "Profile",
        isActive: isActiveTab("Profile"),
        show: true,
      },
    ],
  },
  {
    label: "App Settings",
    show: !isCustomerPortal.value,
    items: [
      {
        label: "Email Notifications",
        icon: MailOpen,
        to: "EmailNotificationsSettings",
        isActive: isActiveTab("EmailNotificationsSettings"),
        show: !isCustomerPortal.value,
      },
      {
        label: "General",
        icon: SettingsGear,
        to: "GeneralSettings",
        isActive: isActiveTab("GeneralSettings"),
        show: !isCustomerPortal.value,
      },
      {
        label: "Email Accounts",
        icon: LucideMail,
        to: "EmailAccounts",
        isActive: isActiveTab("EmailAccounts"),
        show: !isCustomerPortal.value,
      },
      {
        label: "Agents",
        icon: LucideUser,
        to: "Agents",
        isActive: isActiveTab("Agents"),
        show: !isCustomerPortal.value,
      },
      {
        label: "Invite Agent",
        icon: LucideUserPlus,
        to: "InviteAgent",
        isActive: isActiveTab("InviteAgent"),
        show: !isCustomerPortal.value,
      },
      {
        label: "Teams",
        icon: LucideUsers,
        to: "SettingsTeams",
        isActive: isActiveTab("SettingsTeams"),
        show: !isCustomerPortal.value,
      },
      {
        label: "SLA Policies",
        icon: ShieldCheck,
        to: "SLAPolicies",
        isActive: isActiveTab("SLAPolicies"),
        show: !isCustomerPortal.value,
      },
      {
        label: "Business Holidays",
        icon: Briefcase,
        to: "BusinessHolidays",
        isActive: isActiveTab("BusinessHolidays"),
        show: !isCustomerPortal.value,
      },
      {
        label: "Assignment Rules",
        icon: h(Settings, { class: "rotate-90" }),
        to: "AssignmentRules",
        isActive: isActiveTab("AssignmentRules"),
        show: !isCustomerPortal.value,
      },
      {
        label: "Field Dependencies",
        icon: FieldDependencyIcon,
        to: "FieldDependencies",
        isActive: isActiveTab("FieldDependencies"),
        show: !isCustomerPortal.value,
      },
    ],
  },
  {
    label: "Integrations",
    show: !isCustomerPortal.value,
    items: [
      {
        label: "Telephony Settings",
        icon: PhoneIcon,
        to: "TelephonySettings",
        isActive: isActiveTab("TelephonySettings"),
        show: !isCustomerPortal.value,
      },
    ],
  },
];
</script>
