<template>
  <div class="flex flex-col gap-4">
    <!-- title and desc -->
    <div role="heading" aria-level="1" class="flex flex-col gap-1">
      <h5 class="text-lg font-semibold">Setup Email</h5>
      <p class="text-sm text-gray-600">
        Choose the email service provider you want to configure.
      </p>
    </div>
    <!-- email service provider selection -->
    <div class="flex flex-wrap items-center gap-x-24 gap-y-4">
      <div
        v-for="s in services"
        :key="s.name"
        class="min-w-3 flex flex-col items-center gap-1"
        @click="() => (selectedService = s)"
      >
        <div
          class="flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl bg-gray-100 hover:bg-gray-200"
          :class="{
            'ring-2': s.name === selectedService?.name,
            'ring-gray-300': s.name === selectedService?.name,
            'ring-blue-500': s.name === selectedService?.name,
          }"
        >
          <img :src="s.icon" class="h-6 w-6" />
        </div>
        <p class="text-center text-xs text-gray-700">{{ s.name }}</p>
      </div>
    </div>
    <!-- email service provider info -->
    <div
      v-if="selectedService"
      class="flex items-center justify-center gap-2 rounded-md p-2 ring-1 ring-gray-200"
    >
      <IconAlert class="h-8 min-w-[5%] text-blue-500" />
      <div class="text-wrap text-xs text-gray-700">
        {{ selectedService.info }}
        <a
          :href="selectedService.link"
          target="_blank"
          class="text-blue-500 underline"
          >here</a
        >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import IconAlert from "~icons/espresso/alert-circle";
import LogoGmail from "@/assets/images/gmail.png";
import LogoOutlook from "@/assets/images/outlook.png";
import LogoSendgrid from "@/assets/images/sendgrid.png";
import LogoSparkpost from "@/assets/images/sparkpost.webp";
import LogoYahoo from "@/assets/images/yahoo.png";
import LogoYandex from "@/assets/images/yandex.png";

const services = [
  {
    name: "GMail",
    icon: LogoGmail,
    info: `Setting up GMail requires you to enable two factor authentication  
		and app specific passwords. Read more at`,
    link: "https://support.google.com/accounts/answer/185833",
  },
  {
    name: "Outlook",
    icon: LogoOutlook,
    info: `Setting up Outlook requires you to enable two factor authentication 
		and app specific passwords. Read more at`,
    link: "https://support.microsoft.com/en-us/account-billing/how-to-get-and-use-app-passwords-5896ed9b-4263-e681-128a-a6f2979a7944",
  },
  {
    name: "Sendgrid",
    icon: LogoSendgrid,
    info: `Setting up Sendgrid requires you to enable two factor authentication
		and app specific passwords. Read more at `,
    link: "https://sendgrid.com/docs/ui/account-and-settings/two-factor-authentication/",
  },
  {
    name: "SparkPost",
    icon: LogoSparkpost,
    info: `Setting up SparkPost requires you to enable two factor authentication 
		and app specific passwords. Read more at `,
    link: "https://support.sparkpost.com/docs/my-account-and-profile/enabling-two-factor-authentication",
  },
  {
    name: "Yahoo",
    icon: LogoYahoo,
    info: `Setting up Yahoo requires you to enable two factor authentication
		and app specific passwords. Read more at `,
    link: "https://help.yahoo.com/kb/SLN15241.html",
  },
  {
    name: "Yandex",
    icon: LogoYandex,
    info: `Setting up Yandex requires you to enable two factor authentication
		and app specific passwords. Read more at `,
    link: "https://yandex.com/support/id/authorization/app-passwords.html",
  },
];

const selectedService = ref<any | null>(null);
</script>

<style scoped></style>
