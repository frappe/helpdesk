<template>
  <div class="mx-3 pt-6">
    <div class="mb-4 flex items-center justify-between text-base">
      <div class="flex items-center gap-0.5">
        <UserAvatar v-bind="user" size="lg" expand strong />
        <Icon icon="lucide:dot" class="text-gray-500" />
        <!-- <Tooltip :text="dayjs(date).long()"> -->
          <div class="text-gray-600">
             <!-- {{ convert_date(date)}} -->
             {{ get_time_zone(date)}}
          </div>
        <!-- </Tooltip> -->
      </div>
      <slot name="top-right" v-bind="{ message: content }" />
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <span class="prose-f" v-html="sanitize(content)"></span>
    <div class="flex flex-wrap gap-2">
      <AttachmentItem
        v-for="a in attachments"
        :key="a.file_url"
        :label="a.file_name"
        :url="a.file_url"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Tooltip } from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { Icon } from "@iconify/vue";
import { dayjs } from "@/dayjs";
import { UserInfo } from "@/types";
import { AttachmentItem, UserAvatar } from "@/components";
import momentTimezone from "moment-timezone/builds/moment-timezone-with-data-10-year-range.min.js";
import { useUserStore } from "@/stores/user";


const userStore = useUserStore();
const UserDetails = userStore.users.data
const user = userStore.getUser(name);


interface Attachment {
  file_name: string;
  file_url: string;
}

interface P {
  content: string;
  date: string;
  name: string;
  user: UserInfo;
  cc?: string;
  bcc?: string;
  attachments?: Attachment[];
}
withDefaults(defineProps<P>(), {
  cc: () => "",
  bcc: () => "",
  attachments: () => [],
});

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
  });
}

const DefaultTimezone = 'Asia/Riyadh';
const momentTz = {}

function get_time_zone(timeSelected: string){
  UserDetails.forEach(d=> {
    if(d.email == user.email){
      momentTz['date'] = momentTimezone
        .tz(timeSelected, 'YYYY/MM/DD HH:mm', DefaultTimezone)
        .tz(d.time_zone)
        .format('YYYY/MM/DD HH:mm');
      }
  })
  return momentTz['date']
}
// function convert_date(originalTimestamp: string) {
//   const dateObj = new Date(originalTimestamp);
//   const formattedDate = `${dateObj.getFullYear()}-${(dateObj.getMonth() + 1).toString().padStart(2, '0')}-${dateObj.getDate().toString().padStart(2, '0')} ${dateObj.getHours().toString().padStart(2, '0')}:${dateObj.getMinutes().toString().padStart(2, '0')}:${dateObj.getSeconds().toString().padStart(2, '0')}`;
//   return formattedDate;
// }


</script>
