<template>
  <Tabs v-model="tabIndex" :tabs="tabs">
    <TabList />
    <TabPanel v-slot="{ tab }" class="p-5">
      {{ tab }}
    </TabPanel>
  </Tabs>
</template>

<script setup lang="ts">
import { ActivityIcon, CommentIcon, EmailIcon } from "@/components/icons";
import { TabObject } from "@/types";
import { TabList, TabPanel, Tabs } from "frappe-ui";
import { ref } from "vue";

const tabIndex = ref(0);
const tabs: TabObject[] = [
  {
    name: "activity",
    label: "Activity",
    icon: ActivityIcon,
  },
  {
    name: "email",
    label: "Emails",
    icon: EmailIcon,
  },
  {
    name: "comment",
    label: "Comments",
    icon: CommentIcon,
  },
];
</script>

<style scoped></style>
