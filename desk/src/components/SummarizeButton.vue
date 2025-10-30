<template>
  <Button
    title="Summarize ticket activity"
    variant="ghost"
    label="Summarize"
    @click="summarize()"
    class="ml-auto"
    :loading="isSummarizing"
    v-if="showSummarizeButton"
  >
    <template #prefix>
      <SummarizeIcon class="h-4" />
    </template>
  </Button>
</template>

<script setup lang="ts">
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { createResource, toast } from "frappe-ui";
import { onMounted, onUnmounted, ref } from "vue";

const props = defineProps<{
  ticketId: string;
  showSummarizeButton: boolean;
}>();
const emit = defineEmits<{
  (e: "update"): void;
}>();

const { $socket } = globalStore();
const isSummarizing = ref(false);
const summarizationToastId = ref<string | null>(null);
async function summarize() {
  summarizationToastId.value = toast.info(__("Generating summary..."), {
    duration: 60,
  });
  isSummarizing.value = true;
  await createResource({
    url: "helpdesk.api.otto.summary.summarize",
  }).submit({
    ticket_id: props.ticketId,
  });
}

function handleSummarize(data: any) {
  if (data.ticket !== props.ticketId) return;
  if (data.type === "summary") emit("update");
  if (data.type !== "chunk") return;

  // TODO: maintain same toast until summary generation is complete
  const chunk = data.data;
  if (chunk.type === "system" && chunk.message === "end") {
    isSummarizing.value = false;
    toast.remove(summarizationToastId.value);
    toast.success(__("Summary generated"));
    summarizationToastId.value = null;
  }

  if (chunk.type === "system" && chunk.message === "error") {
    isSummarizing.value = false;
    toast.error(__("Error generating summary"));
    console.error(chunk.content);
  }
}

onMounted(() => $socket.on("helpdesk:otto-summarize", handleSummarize));
onUnmounted(() => $socket.off("helpdesk:otto-summarize"));
</script>

<style scoped></style>
