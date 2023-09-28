<template>
  <div
    class="block select-none rounded-[6px] py-[7px] px-[11px]"
    :class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'"
  >
    <div v-if="policy" role="button" class="flex items-center text-base">
      <div class="flex h-[14px] w-[37px] items-center">
        <Input
          type="checkbox"
          :checked="selected"
          role="button"
          @click="$emit('toggleSelect')"
        />
      </div>
      <div class="group flex w-full items-center">
        <RouterLink
          :to="`/settings/sla/${policy.name}`"
          class="flex flex-row items-center space-x-2 truncate pr-10 sm:w-10/12"
        >
          <div>
            {{ policy.name }}
          </div>
          <a title="Default service level agreement">
            <CustomIcons
              v-if="policy.default_sla"
              name="circle-check"
              class="h-[16px] w-[16px] fill-blue-500"
            />
          </a>
        </RouterLink>
        <div class="sm:w-2/12">
          <div class="flex flex-row-reverse">
            <CustomSwitch
              v-model="policy.enabled"
              :disabled="policy.default_sla"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Input, FeatherIcon, Switch } from "frappe-ui";
import CustomIcons from "@/components/desk/global/CustomIcons.vue";

export default {
  name: "SlaPolicyListItem",
  components: {
    Input,
    FeatherIcon,
    CustomSwitch,
    CustomIcons,
  },
  props: ["policy", "selected"],
};
</script>
