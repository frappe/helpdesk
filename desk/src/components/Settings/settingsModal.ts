import { h, markRaw, ref } from "vue";
import Agents from "./Agents.vue";
import Branding from "./Branding.vue";
import EmailConfig from "./EmailConfig.vue";
import TeamsConfig from "./Teams/TeamsConfig.vue";
import Sla from "./Sla/Sla.vue";
import HolidayList from "./Holiday/Holiday.vue";
import FieldDependencyConfig from "./FieldDependency/FieldDependencyConfig.vue";
import InviteAgents from "./InviteAgents.vue";
import ImageUp from "~icons/lucide/image-up";
import LucideMail from "~icons/lucide/mail";
import LucideMailOpen from "~icons/lucide/mail-open";
import LucideUser from "~icons/lucide/user";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucideUsers from "~icons/lucide/users";
import ShieldCheck from "~icons/lucide/shield-check";
import Briefcase from "~icons/lucide/briefcase";
import AssignmentRules from "./Assignment Rules/AssignmentRules.vue";
import Settings from "~icons/lucide/settings-2";
import { FieldDependencyIcon, PhoneIcon } from "@/components/icons";
import Telephony from "./Telephony/Telephony.vue";
import { EmailNotifications } from "./EmailNotifications";
import { __ } from "@/translation";

export const tabs = [
  {
    label: __("Settings"),
    hideLabel: true,
    items: [
      {
        label: "Email Accounts",
        icon: markRaw(LucideMail),
        component: markRaw(EmailConfig),
      },
      {
        label: "Email Notifications",
        icon: markRaw(LucideMailOpen),
        component: markRaw(EmailNotifications),
      },
      {
        label: "Branding",
        icon: markRaw(ImageUp),
        component: markRaw(Branding),
      },
      {
        label: "Agents",
        icon: markRaw(LucideUser),
        component: markRaw(Agents),
      },
      {
        label: "Invite Agents",
        icon: markRaw(LucideUserPlus),
        component: markRaw(InviteAgents),
      },
      {
        label: "Teams",
        icon: markRaw(LucideUsers),
        component: markRaw(TeamsConfig),
      },
      {
        label: "SLA Policies",
        icon: markRaw(ShieldCheck),
        component: markRaw(Sla),
      },
      {
        label: "Business Holidays",
        icon: markRaw(Briefcase),
        component: markRaw(HolidayList),
      },
      {
        label: "Assignment Rules",
        icon: markRaw(h(Settings, { class: "rotate-90" })),
        component: markRaw(AssignmentRules),
      },
      {
        label: "Field Dependencies",
        icon: markRaw(FieldDependencyIcon),
        component: markRaw(FieldDependencyConfig),
      },
    ],
  },
  {
    label: __("Integrations"),
    items: [
      {
        label: "Telephony",
        icon: markRaw(PhoneIcon),
        component: markRaw(Telephony),
      },
    ],
  },
];

export const activeTab = ref(tabs[0].items[0]);

export const nextActiveTab = ref(null);

export const disableSettingModalOutsideClick = ref(false);

export const setActiveSettingsTab = (tabName: string) => {
  activeTab.value =
    (tabName &&
      tabs
        .map((tab) => tab.items)
        .flat()
        .find((tab) => tab.label == tabName)) ||
    tabs[0].items[0];
};
