<template>
  <div class="flex w-[352px] flex-col justify-between border-l">
    <div
      class="h-10.5 flex items-center border-b px-5 py-2.5 text-lg font-semibold"
    >
      About this Ticket
    </div>
    <div class="flex items-center justify-start gap-5 border-b p-5">
      <Avatar
        size="3xl"
        class="h-[88px] w-[88px]"
        :label="'organization?.name'"
        :image="'organization?.organization_logo'"
      />
      <div class="flex flex-col gap-2.5 truncate">
        <Tooltip :text="organization?.name">
          <div class="truncate text-2xl font-medium">organization?.name</div>
        </Tooltip>
        <div class="flex gap-1.5">
          <Tooltip text="Make a call...">
            <Button
              class="h-7 w-7"
              @click="
                () =>
                  deal.data.mobile_no
                    ? makeCall(deal.data.mobile_no)
                    : errorMessage('No mobile number set')
              "
            >
              <PhoneIcon class="h-4 w-4" />
            </Button>
          </Tooltip>
          <Button class="h-7 w-7">
            <EmailIcon
              class="h-4 w-4"
              @click="
                deal.data.email ? openEmailBox() : errorMessage('No email set')
              "
            />
          </Button>
          <Tooltip text="Go to website...">
            <Button class="h-7 w-7">
              <LinkIcon
                class="h-4 w-4"
                @click="
                  deal.data.website
                    ? openWebsite(deal.data.website)
                    : errorMessage('No website set')
                "
              />
            </Button>
          </Tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";
import { EmailIcon, PhoneIcon, LinkIcon } from "@/components/icons/";
</script>
