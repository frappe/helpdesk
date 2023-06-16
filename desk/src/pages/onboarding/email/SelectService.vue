<template>
  <div class="flex flex-col gap-4">
    <div class="text-gray-700">
      {{ title }}
    </div>
    <div class="grid grid-cols-4 gap-4">
      <div
        v-for="s in services"
        :key="s.name"
        class="flex h-20 w-20 cursor-pointer items-center justify-center place-self-center rounded-xl bg-gray-100 hover:bg-gray-200"
        :class="{
          'ring-2': s.name === service,
          'ring-gray-300': s.name === service,
        }"
        @click="service = s.name"
      >
        <Tooltip :text="s.name">
          <img :src="s.icon" class="h-12 w-12" />
        </Tooltip>
      </div>
    </div>
    <div
      v-if="info"
      class="flex items-center gap-2 rounded-xl p-2 ring-1 ring-gray-200"
    >
      <IconAlert class="h-12 w-12 text-blue-500" />
      <div class="text-xs text-gray-700">
        {{ info }}
      </div>
    </div>
    <Button
      label="Continue"
      :disabled="isEmpty(service)"
      class="w-max"
      variant="outline"
      @click="next"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { Button, Tooltip } from "frappe-ui";
import { isEmpty } from "lodash";
import { capture } from "@/telemetry";
import { useOnboardingEmailStore } from "./data";
import IconAlert from "~icons/espresso/alert-circle";
import LogoGmail from "@/assets/images/gmail.png";
import LogoOutlook from "@/assets/images/outlook.png";
import LogoSendgrid from "@/assets/images/sendgrid.png";
import LogoSparkpost from "@/assets/images/sparkpost.webp";
import LogoYahoo from "@/assets/images/yahoo.png";
import LogoYandex from "@/assets/images/yandex.png";

const onboardingEmailStore = useOnboardingEmailStore();
const { next } = onboardingEmailStore;
const { service } = storeToRefs(onboardingEmailStore);
const title = "Which service do you want to add?";
const services = [
  {
    name: "GMail",
    icon: LogoGmail,
    info: "Setting up GMail requires you to enable two factor authentication \
		and app specific passwords. Read more at https://support.google.com/accounts/answer/185833",
  },
  {
    name: "Outlook",
    icon: LogoOutlook,
  },
  {
    name: "Sendgrid",
    icon: LogoSendgrid,
  },
  {
    name: "SparkPost",
    icon: LogoSparkpost,
  },
  {
    name: "Yahoo",
    icon: LogoYahoo,
  },
  {
    name: "Yandex",
    icon: LogoYandex,
  },
];
const info = computed(
  () => services.find((s) => s.name === service.value)?.info
);

onMounted(() => capture("onboarding_email_select_service_reached"));
</script>
