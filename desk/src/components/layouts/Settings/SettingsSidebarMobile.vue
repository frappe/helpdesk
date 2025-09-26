<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" @close="sidebarOpened = false" class="fixed inset-0 z-40">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
        <div
          class="relative z-10 flex h-full w-[230px] flex-col border-r bg-gray-50 transition-all duration-300 ease-in-out p-2"
        >
          <div class="flex items-center gap-2">
            <Button
              icon="arrow-left"
              @click="() => router.push({ name: 'TicketsAgent' })"
              variant="ghost"
              class="ml-0.5"
            />
            <div class="text-base text-ink-gray-8">Settings</div>
          </div>
          <div v-for="section in links">
            <div v-if="isExpanded" class="text-base text-ink-gray-5 my-2.5">
              <span class="w-full overflow-clip text-nowrap">{{
                section.label
              }}</span>
            </div>
            <div v-for="item in section.items">
              <SidebarLink
                class="relative my-0.5 min-h-7"
                :label="item.label"
                :icon="item.icon"
                :to="item.to"
                :is-active="isActiveTab(item.to)"
                :is-expanded="isExpanded"
                @click="sidebarOpened = false"
              />
            </div>
          </div>
        </div>
      </TransitionChild>
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <DialogOverlay class="fixed inset-0 bg-gray-600 bg-opacity-50" />
      </TransitionChild>
    </Dialog>
  </TransitionRoot>
</template>
<script setup lang="ts">
import {
  Dialog,
  DialogOverlay,
  TransitionChild,
  TransitionRoot,
} from "@headlessui/vue";
import { FieldDependencyIcon, PhoneIcon } from "@/components/icons";
import { h } from "vue";

import { useRoute, useRouter } from "vue-router";

import SidebarLink from "@/components/SidebarLink.vue";

import { mobileSidebarOpened as sidebarOpened } from "@/composables/mobile";

import LucideMail from "~icons/lucide/mail";
import MailOpen from "~icons/lucide/mail-open";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucideUser from "~icons/lucide/user";
import LucideChevronLeft from "~icons/lucide/chevron-left";
import ShieldCheck from "~icons/lucide/shield-check";
import Briefcase from "~icons/lucide/briefcase";
import Settings from "~icons/lucide/settings-2";
import LucideUsers from "~icons/lucide/users";
import SettingsGear from "~icons/lucide/settings";

import { storeToRefs } from "pinia";
import { useSidebarStore } from "@/stores/sidebar";
import { isCustomerPortal } from "@/utils";
import { Button } from "frappe-ui";

const { isExpanded } = storeToRefs(useSidebarStore());
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

    items: [
      {
        label: "Profile",
        icon: LucideUser,
        to: "Profile",
        isActive: isActiveTab("Profile"),
      },
    ],
  },
  {
    label: "App Settings",

    items: [
      {
        label: "Email Notifications",
        icon: MailOpen,
        to: "EmailNotificationsSettings",
        isActive: isActiveTab("EmailNotificationsSettings"),
      },
      {
        label: "General",
        icon: SettingsGear,
        to: "GeneralSettings",
        isActive: isActiveTab("GeneralSettings"),
      },
      {
        label: "Email Accounts",
        icon: LucideMail,
        to: "EmailAccounts",
        isActive: isActiveTab("EmailAccounts"),
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

    items: [
      {
        label: "Telephony Settings",
        icon: PhoneIcon,
        to: "TelephonySettings",
        isActive: isActiveTab("TelephonySettings"),
      },
    ],
  },
];
</script>
