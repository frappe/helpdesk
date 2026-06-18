<template>
  <div v-if="customers?.length" class="flex items-center gap-1.5">
    <div class="flex items-center">
      <Tooltip
        v-for="customer in customers"
        :key="customer.name"
        :text="customer.name"
      >
        <Avatar
          class="-mr-1.5 cursor-pointer ring-2 ring-[var(--surface-white)] transition hover:z-10 hover:scale-110"
          shape="circle"
          size="sm"
          :image="customer.image"
          :label="customer.name"
          @click="goToCustomer(customer.name)"
        />
      </Tooltip>
    </div>
    <span class="cursor-pointer text-sm text-ink-gray-8 ml-2">
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

const label = computed(() =>
  props.customers.length === 1
    ? props.customers[0].name
    : __("{0} Customers", [props.customers.length])
);

function goToCustomer(name: string): void {
  router.push({ name: "Customer", params: { id: name } });
}
</script>
