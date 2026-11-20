<template>
  <template v-if="whatsNew">
    <Button
      v-if="isSidebarCollapsed"
      variant="ghost"
      icon="lucide-sparkles"
      :tooltip="whatsNew.title"
      :aria-label="whatsNew.title"
      @click="openModal"
    />
    <SidebarCard
      v-else
      icon="lucide-sparkles"
      :title="__('What\'s new')"
      :description="whatsNew.title"
      dismissible
      :action="{ label: __('See what\'s new'), onClick: openModal }"
      @dismiss="markSeen"
    />
  </template>
</template>

<script setup lang="ts">
import { mobileSidebarOpened } from "@/composables/mobile";
import { useBanners } from "@/composables/useBanners";
import { useWhatsNewModal } from "@/composables/useWhatsNewModal";
import { __ } from "@/translation";
import { Button, SidebarCard, toast } from "frappe-ui";
import { computed } from "vue";

defineProps<{ isSidebarCollapsed?: boolean }>();

const { banner, dismiss } = useBanners();
const { show } = useWhatsNewModal();

const whatsNew = computed(() => banner("whats_new"));

async function openModal() {
  show(whatsNew.value?.releases ?? []);
  // The phone drawer would sit under the sheet
  mobileSidebarOpened.value = false;
  await markSeen();
}

async function markSeen() {
  try {
    await dismiss("whats_new");
  } catch {
    toast.error(__("Couldn't hide this notice. Please try again."));
  }
}
</script>
