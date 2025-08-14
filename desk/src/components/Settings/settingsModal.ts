import { h, markRaw, ref } from "vue";
import ImageUp from "~icons/lucide/image-up";
import LucideMail from "~icons/lucide/mail";
import LucideUser from "~icons/lucide/user";
import LucideUsers from "~icons/lucide/users";
import ShieldCheck from "~icons/lucide/shield-check";
import Briefcase from "~icons/lucide/briefcase";
import Agents from "./Agents.vue";
import Branding from "./Branding.vue";
import EmailConfig from "./EmailConfig.vue";
import TeamsConfig from "./Teams/TeamsConfig.vue";
import Sla from "./Sla/Sla.vue";
import HolidayList from "./Holiday/Holiday.vue";
import FieldDependencyConfig from "./FieldDependency/FieldDependencyConfig.vue";
import { FieldDependencyIcon } from "@/components/icons";
import AssignmentRules from "./Assignment Rules/AssignmentRules.vue";
import Settings from "~icons/lucide/settings-2";

export const tabs = [
  {
    label: "Email Accounts",
    icon: markRaw(LucideMail),
    component: markRaw(EmailConfig),
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
    label: "Field Dependencies",
    icon: markRaw(FieldDependencyIcon),
    component: markRaw(FieldDependencyConfig),
  },
  {
    label: "Assignment Rules",
    icon: markRaw(h(Settings, { class: "rotate-90" })),
    component: markRaw(AssignmentRules),
  },
];

export const activeTab = ref(tabs[0]);

export const disableSettingModalOutsideClick = ref(false);

export const setActiveSettingsTab = (tab: string) => {
  activeTab.value = tabs.find((t) => t.label === tab);
};
