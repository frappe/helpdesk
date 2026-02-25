<template>
  <div class="flex items-center justify-between p-5 pb-0">
    <div class="gap-x-3 flex">
      <Avatar
        size="3xl"
        shape="square"
        :label="customer.doc.customer_name"
        :image="customer.doc.image"
        class="h-[52px] w-[52px]"
      />
      <div class="flex flex-col h-full">
        <p class="font-medium text-ink-gray-8 text-xl mb-1.5">
          {{ customer.doc.customer_name }}
        </p>
        <div class="flex items-center gap-x-1.5">
          <template v-for="(item, index) in customerInfo" :key="index">
            <template v-if="item.condition">
              <span
                v-if="customerInfo.slice(0, index).some((i) => i.condition)"
                class="text-ink-gray-4"
                >•</span
              >
              <div class="flex items-center gap-x-1">
                <component :is="item.icon" class="h-4 w-4 text-ink-gray-6" />
                <span class="text-sm text-ink-gray-8">{{ item.value }}</span>
              </div>
            </template>
          </template>
        </div>
      </div>
    </div>
    <Button label="Edit" @click="customerDialog = true" v-if="hasPermission()">
      <div class="flex gap-1">
        <LucideSquarePen class="h-4 w-4" />
        <span>{{ __("Edit") }}</span>
      </div>
    </Button>
  </div>
  <!-- TODO: refactor this dialog -->
  <CustomerDialog
    v-if="customerDialog"
    v-model="customerDialog"
    :name="customer.doc.customer_name"
    @update="customerDialog = false"
  />
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import { hasPermission } from "@/utils";
import { Avatar, Button } from "frappe-ui";
import { computed, inject, markRaw, ref } from "vue";
import LucideGlobe from "~icons/lucide/globe";
import LucideMail from "~icons/lucide/mail";
import LucidePhone from "~icons/lucide/phone";
import LucideSquarePen from "~icons/lucide/square-pen";
import LucideSquareUser from "~icons/lucide/square-user";
import CustomerDialog from "./CustomerDialog.vue";

const customer = inject(CustomerResourceSymbol)!;

const customerDialog = ref(false);

const customerInfo = computed(() => [
  // lucideglobe which takes domain of props.customer.domain
  {
    icon: markRaw(LucideGlobe),
    value: customer.doc.domain,
    condition: !!customer.doc.domain,
  },
  {
    icon: markRaw(LucideMail),
    value: customer.doc.email_id,
    condition: !!customer.doc.email_id,
  },
  {
    icon: markRaw(LucidePhone),
    value: customer.doc.mobile_no,
    condition: !!customer.doc.mobile_no,
  },
  {
    icon: markRaw(LucideSquareUser),
    value: `${customer.doc.contacts?.length ?? 0} ${
      customer.doc.contacts?.length === 1 ? __("contact") : __("contacts")
    }`,
    condition: true,
  },
]);
</script>
