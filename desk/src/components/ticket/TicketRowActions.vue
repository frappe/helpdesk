<template>
  <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
    <Tooltip :text="assignedToMe ? 'Unassign from me' : 'Assign to me'">
      <Button
        variant="ghost"
        @click.stop="toggleAssignment"
        :loading="loading"
        class="!p-1"
      >
        <template #icon>
          <LucideUserCheck v-if="assignedToMe" class="size-4 text-blue-600" />
          <LucideUserPlus v-else class="size-4" />
        </template>
      </Button>
    </Tooltip>
    
    <Tooltip text="Mark as Resolved" v-if="canResolve">
      <Button
        variant="ghost"
        @click.stop="resolveTicket"
        :loading="loading"
        class="!p-1"
      >
        <template #icon>
          <LucideCheckCircle class="size-4 text-green-600" />
        </template>
      </Button>
    </Tooltip>
    
    <Dropdown :options="moreActions" placement="left">
      <Button variant="ghost" class="!p-1">
        <template #icon>
          <LucideMoreVertical class="size-4" />
        </template>
      </Button>
    </Dropdown>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { Button, call, Dropdown, toast, Tooltip } from "frappe-ui";
import { computed, ref } from "vue";
import LucideCheckCircle from "~icons/lucide/check-circle";
import LucideMoreVertical from "~icons/lucide/more-vertical";
import LucideUserCheck from "~icons/lucide/user-check";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucideX from "~icons/lucide/x";

interface Props {
  ticket: any;
  onUpdate?: () => void;
}

const props = defineProps<Props>();
const emit = defineEmits(["update"]);

const { userId } = useAuthStore();
const loading = ref(false);

const assignedToMe = computed(() => {
  if (!props.ticket._assign) return false;
  try {
    const assignees = JSON.parse(props.ticket._assign);
    return assignees.includes(userId);
  } catch {
    return false;
  }
});

const canResolve = computed(() => {
  return props.ticket.status_category !== "Resolved";
});

async function toggleAssignment() {
  loading.value = true;
  try {
    if (assignedToMe.value) {
      await call("frappe.desk.form.assign_to.remove", {
        doctype: "HD Ticket",
        name: props.ticket.name,
        assign_to: userId,
      });
      toast({
        title: "Unassigned from you",
        icon: "check",
        iconClasses: "text-green-500",
      });
    } else {
      await call("frappe.desk.form.assign_to.add", {
        doctype: "HD Ticket",
        name: props.ticket.name,
        assign_to: [userId],
      });
      toast({
        title: "Assigned to you",
        icon: "check",
        iconClasses: "text-green-500",
      });
    }
    emit("update");
  } catch (error: any) {
    toast({
      title: "Failed",
      text: error.message,
      icon: "x",
      iconClasses: "text-red-500",
    });
  } finally {
    loading.value = false;
  }
}

async function resolveTicket() {
  loading.value = true;
  try {
    await call("frappe.client.set_value", {
      doctype: "HD Ticket",
      name: props.ticket.name,
      fieldname: "status",
      value: "Resolved",
    });
    toast({
      title: "Ticket resolved",
      icon: "check",
      iconClasses: "text-green-500",
    });
    emit("update");
  } catch (error: any) {
    toast({
      title: "Failed to resolve",
      text: error.message,
      icon: "x",
      iconClasses: "text-red-500",
    });
  } finally {
    loading.value = false;
  }
}

async function closeTicket() {
  loading.value = true;
  try {
    await call("frappe.client.set_value", {
      doctype: "HD Ticket",
      name: props.ticket.name,
      fieldname: "status",
      value: "Closed",
    });
    toast({
      title: "Ticket closed",
      icon: "check",
      iconClasses: "text-green-500",
    });
    emit("update");
  } catch (error: any) {
    toast({
      title: "Failed to close",
      text: error.message,
      icon: "x",
      iconClasses: "text-red-500",
    });
  } finally {
    loading.value = false;
  }
}

async function reopenTicket() {
  loading.value = true;
  try {
    await call("frappe.client.set_value", {
      doctype: "HD Ticket",
      name: props.ticket.name,
      fieldname: "status",
      value: "Open",
    });
    toast({
      title: "Ticket reopened",
      icon: "check",
      iconClasses: "text-green-500",
    });
    emit("update");
  } catch (error: any) {
    toast({
      title: "Failed to reopen",
      text: error.message,
      icon: "x",
      iconClasses: "text-red-500",
    });
  } finally {
    loading.value = false;
  }
}

const moreActions = computed(() => {
  const actions = [];
  
  if (props.ticket.status_category === "Resolved") {
    actions.push({
      label: "Reopen",
      icon: "rotate-ccw",
      onClick: reopenTicket,
    });
  } else {
    actions.push({
      label: "Close",
      icon: () => h(LucideX, { class: "size-4" }),
      onClick: closeTicket,
    });
  }
  
  return actions;
});
</script>

