import { FieldDependencyIcon, PhoneIcon } from "@/components/icons";
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { Avatar } from "frappe-ui";
import { computed, h, markRaw, ref } from "vue";
import Briefcase from "~icons/lucide/briefcase";
import LucideMail from "~icons/lucide/mail";
import LucideMailOpen from "~icons/lucide/mail-open";
import SettingsGear from "~icons/lucide/settings";
import Settings from "~icons/lucide/settings-2";
import ShieldCheck from "~icons/lucide/shield-check";
import LucideUser from "~icons/lucide/user";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucideUsers from "~icons/lucide/users";
import Agents from "./Agents.vue";
import AssignmentRules from "./Assignment Rules/AssignmentRules.vue";
import EmailConfig from "./EmailConfig.vue";
import { EmailNotifications } from "./EmailNotifications";
import FieldDependencyConfig from "./FieldDependency/FieldDependencyConfig.vue";
import General from "./General/General.vue";
import HolidayList from "./Holiday/Holiday.vue";
import InviteAgents from "./InviteAgents.vue";
import Profile from "./Profile/Profile.vue";
import Sla from "./Sla/Sla.vue";
import TeamsConfig from "./Teams/TeamsConfig.vue";
import Telephony from "./Telephony/Telephony.vue";

const auth = useAuthStore();

export const tabs = computed(() => {
  const _tabs = [
    {
      label: __("User Settings"),
      hideLabel: true,
      items: [
        {
          label: __("Profile"),
          icon: h(Avatar, {
            image: auth.userImage,
            label: auth.userName,
            size: "xs",
          }),
          component: markRaw(Profile),
        },
      ],
    },
    {
      label: __("Email Settings"),
      condition: () => auth.isAdmin || auth.isManager,
      items: [
        {
          label: __("Email Accounts"),
          icon: markRaw(LucideMail),
          component: markRaw(EmailConfig),
        },
        {
          label: __("Email Notifications"),
          icon: markRaw(LucideMailOpen),
          component: markRaw(EmailNotifications),
        },
      ],
    },
    {
      label: __("App Settings"),
      condition: () => auth.isAdmin || auth.isManager,
      items: [
        {
          label: __("General"),
          icon: markRaw(SettingsGear),
          component: markRaw(General),
          condition: () => auth.isAdmin,
        },
        {
          label: __("Agents"),
          icon: markRaw(LucideUser),
          component: markRaw(Agents),
        },
        {
          label: __("Invite Agents"),
          icon: markRaw(LucideUserPlus),
          component: markRaw(InviteAgents),
        },
        {
          label: __("Teams"),
          icon: markRaw(LucideUsers),
          component: markRaw(TeamsConfig),
        },
        {
          label: __("SLA Policies"),
          icon: markRaw(ShieldCheck),
          component: markRaw(Sla),
        },
        {
          label: __("Business Holidays"),
          icon: markRaw(Briefcase),
          component: markRaw(HolidayList),
        },
        {
          label: __("Assignment Rules"),
          icon: markRaw(h(Settings, { class: "rotate-90" })),
          component: markRaw(AssignmentRules),
        },
        {
          label: __("Field Dependencies"),
          icon: markRaw(FieldDependencyIcon),
          component: markRaw(FieldDependencyConfig),
        },
      ],
    },
    {
      label: __("Integrations"),
      items: [
        {
          label: __("Telephony"),
          icon: markRaw(PhoneIcon),
          component: markRaw(Telephony),
        },
      ],
    },
  ];

  return _tabs.filter((tab) => {
    if (tab.condition && !tab.condition()) return false;
    if (tab.items) {
      tab.items = tab.items.filter((item) => {
        if (item.condition && !item.condition()) return false;
        return true;
      });
    }
    return true;
  });
});

export const activeTab = ref(tabs.value[0].items[0]);

export const nextActiveTab = ref(null);

export const disableSettingModalOutsideClick = ref(false);

type TabName =
  | "Profile"
  | "Email Accounts"
  | "Email Notifications"
  | "General"
  | "Agents"
  | "Invite Agents"
  | "Teams"
  | "SLA Policies"
  | "Business Holidays"
  | "Assignment Rules"
  | "Field Dependencies"
  | "Telephony";

export const setActiveSettingsTab = (tabName: TabName) => {
  activeTab.value =
    (tabName &&
      tabs.value
        .map((tab) => tab.items)
        .flat()
        .find((tab) => tab.label == __(tabName))) ||
    tabs.value[0].items[0];
};
