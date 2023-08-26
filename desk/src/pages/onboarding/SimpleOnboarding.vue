<template>
  <div class="flex h-screen w-screen items-center justify-center bg-gray-100">
    <div class="container-box w-1/3 rounded-xl text-base text-gray-900">
      <div class="rounded-t-xl bg-white px-8 py-6">
        <div class="mb-4 text-xl font-semibold">
          {{ steps[step]["title"] }}
        </div>
        <component :is="steps[step]['component']" />
      </div>
      <div class="flex justify-end rounded-b-xl bg-gray-200 px-8 py-3">
        <Button
          v-for="action in actions"
          :key="action.label"
          :label="action.label"
          :variant="action.variant"
          @click="action.onClick"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeMount, ref } from "vue";
import { useRouter } from "vue-router";
import { createResource } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import OnboardingIntro from "./OnboardingIntro.vue";
import SetupEmail from "./email/SetupEmail.vue";
import SetupFavicon from "./SetupFavicon.vue";
import SetupLogo from "./SetupLogo.vue";
import SetupName from "./SetupName.vue";
import SetupSkipEmail from "./SetupSkipEmail.vue";
import SuccessMessage from "./SuccessMessage.vue";

const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();
const step = ref(0);
const steps = [
  {
    title: "Welcome to Frappe Helpdesk! 🎉",
    component: OnboardingIntro,
  },
  {
    title: "Begin with a name! 🖋️",
    component: SetupName,
  },
  {
    title: "Let's set a logo 💫",
    component: SetupLogo,
  },
  {
    title: "How about a Favicon? 🌏",
    component: SetupFavicon,
  },
  {
    title: "Did you know? 💡",
    component: SetupSkipEmail,
  },
  {
    title: "Let's setup an email 📬",
    component: SetupEmail,
  },
  {
    title: "That's it for now! 🙏",
    component: SuccessMessage,
  },
];
const actions = computed(() =>
  [
    {
      label: "← Previous",
      appearance: "minimal",
      variant: "ghost",
      onClick() {
        step.value--;
      },
      condition: step.value + 1 > 1 && step.value + 1 <= steps.length,
    },
    {
      label: "Next →",
      appearance: "primary",
      variant: "solid",
      onClick() {
        step.value++;
      },
      condition: step.value + 1 < steps.length,
    },
    {
      label: "Finish ✓",
      variant: "solid",
      onClick() {
        finish();
      },
      condition: step.value + 1 === steps.length,
    },
  ].filter((a) => a.condition)
);

function finish() {
  createResource({
    url: "frappe.client.set_value",
  })
    .submit({
      doctype: "HD Settings",
      name: "HD Settings",
      fieldname: "setup_complete",
      value: true,
    })
    .then(redirect);
}

function redirect() {
  router.replace({ path: '/' });
}

onBeforeMount(() => {
  if (!authStore.hasDeskAccess || configStore.isSetupComplete) {
    redirect();
  }
});
</script>

<style scoped>
.container-box {
  box-shadow: rgba(0, 0, 0, 0.16) 0px 10px 36px 0px,
    rgba(0, 0, 0, 0.06) 0px 0px 0px 1px;
}
</style>
