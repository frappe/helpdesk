<template>
  <div v-if="customers?.length" class="flex items-center gap-1.5">
    <div class="flex items-center">
      <Tooltip
        v-for="customer in visibleCustomers"
        :key="customer.name"
        :text="customer.name"
      >
        <Avatar
          class="-mr-1.5 cursor-pointer ring-2 ring-[var(--surface-base)] transition hover:z-10 hover:scale-110"
          shape="circle"
          size="sm"
          :image="customer.image"
          :label="customer.name"
          @click="goToCustomer(customer.name)"
        />
      </Tooltip>
      <div
        v-if="remainingCustomers.length"
        class="relative -mr-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-surface-gray-2 text-2xs font-medium text-ink-gray-6 ring-2 ring-[var(--surface-white)]"
      >
        +{{ remainingCustomers.length }}
      </div>
    </div>
    <span
      class="text-sm text-ink-gray-8 ml-2"
      :class="customers.length === 1 && 'cursor-pointer'"
      v-on="
        customers.length === 1
          ? { click: () => goToCustomer(customers[0]!.name) }
          : {}
      "
    >
      {{ label }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Avatar, Tooltip } from "frappe-ui";
import { computed } from "vue";
import { useRouter } from "vue-router";

interface Customer {
  name: string;
  image?: string | null;
}

const props = defineProps<{
  customers: Customer[];
}>();

const router = useRouter();

const MAX_VISIBLE_AVATARS = 5;

const visibleCustomers = computed(() =>
  props.customers.slice(0, MAX_VISIBLE_AVATARS)
);

const remainingCustomers = computed(() =>
  props.customers.slice(MAX_VISIBLE_AVATARS)
);

const label = computed(() =>
  props.customers.length === 1
    ? props.customers[0].name
    : __("{0} Customers", [props.customers.length])
);

function goToCustomer(name: string): void {
  router.push({ name: "Customer", params: { id: name } });
}
</script>
