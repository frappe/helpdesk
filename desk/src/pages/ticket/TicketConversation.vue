<template>
  <div
      class="mx-6 md:mx-10 md:my-2 flex items-center justify-between text-lg font-medium mb-4 !mt-8"
  >
    Activity
    <!-------Record Screen---------->
    <div>
      <Button
          :variant="'outline'"
          :ref_for="true"
          theme="gray"
          size="sm"
          :loading="false"
          :loadingText="null"
          :disabled="false"
          :link="null"
          v-if="!isRecording"
          @click="startRecording"
      >
        <div class="flex items-center gap-2">
          <Icon icon="gala:video" class="text-green-600"/>
          Record Screen
        </div>
      </Button>
      <Button
          :variant="'outline'"
          :ref_for="true"
          theme="gray"
          size="sm"
          :loading="false"
          :loadingText="null"
          :disabled="false"
          :link="null"
          v-if="isRecording"
          @click="stopRecording"
      >
        <div class="flex items-center gap-2">
          <Icon icon="mdi:stop-circle" class="text-red-600"/>
          Stop Recording
        </div>
      </Button>
      <!-------Record Screen---------->
    </div>

  </div>
  <div class="overflow-auto px-6 md:px-10 grow">
    <div
        v-for="(c, i) in communications"
        :id="c.name"
        :key="c.name"
        class="flex items-between justify-center gap-4 relative"
        :class="i === 0 && 'mt-4'"
    >
      <div
          class="w-full activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4 h-full"
      >
        <div
            class="relative flex justify-center after:absolute after:left-[50%] after:top-3 after:-z-10 after:border-l after:border-gray-200"
            :class="[
            i != communications.length - 1 ? 'after:h-full' : 'after:h-5',
          ]"
        >
          <Avatar
              size="lg"
              :label="c.user.name"
              :image="c.user.image"
              class="mt-1.5 relative"
          />
        </div>
        <TicketCommunication
            :content="c.content"
            :date="c.creation"
            :user="c.user"
            :sender-image="c.sender"
            :cc="c.cc || ''"
            :bcc="c.bcc || ''"
            :attachments="c.attachments"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { dayjs } from "@/dayjs";
import { Avatar, toast, createResource } from "frappe-ui";
import { orderBy } from "lodash";
import { computed, inject, nextTick, watch, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import TicketCommunication from "./TicketCommunication.vue";
import { ITicket } from "./symbols";
import { Icon } from "@iconify/vue";

interface P {
  focus?: string;
}

const props = withDefaults(defineProps<P>(), {
  focus: "",
});
const router = useRouter()
const route = useRoute();
const ticket = inject(ITicket);
const communications = computed(() => {
  const _communications = ticket.data.communications || [];
  return orderBy(_communications, (c) => dayjs(c.creation));
});

function isElementInViewport(el: HTMLElement) {
  if (!el) return false;
  const rect = el.getBoundingClientRect();
  return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= window.innerHeight &&
      rect.right <= window.innerWidth
  );
}

function scroll(id: string) {
  const e = document.getElementById(id);
  if (!isElementInViewport(e)) {
    e.scrollIntoView();
  }
}

/*Record Screen*/

const emit = defineEmits(["update", "reload"]);
const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordedChunks: Blob[] = []
const videoRef = ref<HTMLVideoElement | null>(null)
let currentStream: MediaStream | null = null

async function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({video: true, audio: true})
    currentStream = stream
    mediaRecorder.value = new MediaRecorder(stream)

    recordedChunks.length = 0

    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunks.push(event.data)
      }
    }

    mediaRecorder.value.onstop = async () => {
      const blob = new Blob(recordedChunks, {type: 'video/webm'})
      const file = new File([blob], 'recording.webm', {type: 'video/webm'})

      // Stop screen sharing
      currentStream?.getTracks().forEach(track => track.stop())
      currentStream = null

      // Preview video
      const url = URL.createObjectURL(blob)
      if (videoRef.value) videoRef.value.src = url

      // Upload to Frappe
      const base64Data = await blobToBase64(blob)
      const docname = communications.value[0]?.name;
      const ticket_record_video = createResource({
        url: "helpdesk.api.ticket.save_record_video",
        debounce: 300,
        makeParams: () => ({
          docname: docname,
          file_data: base64Data,
          ticket_id: ticket.data.name
        }),
        validate: (params: any) => {
        },
        onSuccess: async (data: any) => {
          toast.success("Recorded video has been saved");
          ticket.reload();
        },
      });
      ticket_record_video.submit();
      isRecording.value = false
    }
    mediaRecorder.value.start()
    isRecording.value = true;
    //await router.replace({path: route.fullPath, query: route.query})
  } catch (err) {
    console.error('Failed to start screen recording:', err)
  }
}

const stopRecording = () => {
  mediaRecorder.value?.stop()
  isRecording.value = false
}

/*Record Screen*/

watch(
    () => props.focus,
    (id: string) => scroll(id)
);
nextTick(() => {
  const hash = route.hash.slice(1);
  const id = hash || communications.value.slice(-1).pop()?.name;
  if (id) setTimeout(() => scroll(id), 1000);
});
</script>
