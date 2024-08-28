<template>
  <div
    class="block select-none rounded-[6px] py-[7px] px-[11px]"
    :class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'"
  >
    <div
      v-if="canned_response"
      role="button"
      class="flex items-center text-base"
    >
      <div class="flex h-[14px] w-[37px] items-center">
        <Input
          type="checkbox"
          @click="$emit('toggleSelect')"
          :checked="selected"
          role="button"
        />
      </div>
      <RouterLink
        :to="`/settings/canned_responses/${canned_response.name}`"
        class="group flex w-full items-center"
      >
        <div class="truncate pr-10 sm:w-10/12">
          {{ canned_response.title }}
        </div>
        <div class="truncate pr-10 sm:w-2/12">
          {{ canned_response.owner }}
        </div>
        <div class="truncate sm:w-2/12"></div>
      </RouterLink>
    </div>
  </div>
</template>

<script>
import { Input, FeatherIcon } from "frappe-ui";
import Badge from "frappe-ui/src/components/Badge.vue";
export default {
  name: "CannedResponseListItem",
  props: ["canned_response", "selected"],
  components: {
    Input,
    FeatherIcon,
    Badge,
  },
};
</script>
