<template>
  <div class="flex items-center justify-between px-5 py-3 border-b flex-shrink-0">
    <h3 class="text-base font-semibold text-ink-gray-9">{{ title }}</h3>

    <Button
      v-if="title === __('Tasks')"
      variant="subtle"
      @click="showNewTaskModal = true"
    >
      <template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
      {{ __('New') }}
    </Button>

    <Button
      v-else-if="title === __('Emails')"
      variant="subtle"
      @click="emit('new-email')"
    >
      <template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
      {{ __('New') }}
    </Button>
  </div>

  <TaskboxEditor
    v-model="showNewTaskModal"
    :ticket-id="resolvedTicketId"
    @submit="() => { showNewTaskModal = false; emit('update') }"
  />

  <FadedScrollableDiv class="flex flex-col flex-1 overflow-y-auto" :mask-length="20">
    <div v-if="activities.length" class="activities flex-1 h-full mt-0.5">
      <div
        v-for="(activity, i) in localActivities"
        :key="activity.key"
        class="activity mt-2"
        tabindex="0"
      >
        <div class="w-full px-6 md:px-5 grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4">
          <!-- Timeline icon -->
          <div
            class="relative flex justify-center after:absolute after:left-[50%] after:top-3 after:-z-10 after:border-l after:border-gray-200"
            :class="[
              i !== activities.length - 1 && 'after:h-full',
              !['email','feedback','call','comment','task'].includes(activity.type) && 'after:top-6',
            ]"
          >
            <div
              class="z-1 flex items-center justify-center rounded-full bg-surface-white"
              :class="[
                ['email','feedback'].includes(activity.type) ? 'my-1 h-9 w-9' : 'h-6 w-6',
                !['email','feedback','call','comment','task'].includes(activity.type) && 'mt-[2px]',
              ]"
            >
              <Avatar
                v-if="activity.type === 'email' || activity.type === 'feedback'"
                size="lg"
                :label="activity.sender?.full_name"
                :image="getUser(activity.sender?.name).user_image"
                class="bg-surface-white absolute left-[0.7px]"
              />
              <CommentIcon
                v-else-if="activity.type === 'comment'"
                class="text-gray-600 absolute left-[7.5px]"
              />
              <FeatherIcon
                v-else-if="activity.type === 'task'"
                name="check-square"
                class="text-gray-600 left-[7.5px] size-4"
              />
              <FeatherIcon
                v-else-if="activity.type === 'call'"
                :name="activity.call_type === 'Incoming' ? 'phone-incoming' : 'phone-outgoing'"
                class="text-gray-600 left-[7.5px] size-4"
              />
              <TaskIcon
               v-else-if="activity.type == 'task'"
               :name="check-square"
              class="text-gray-600 left-[7.5px] size-4"
              />
              <DotIcon v-else class="text-gray-600 absolute left-[7.5px] top-[6px]" />
            </div>
          </div>
          <div
            class="mb-4 flex flex-1"
            :class="[
              i === activities.length - 1 && 'mb-5',
              !['email','feedback','call','comment','task'].includes(activity.type) && 'mt-[2px]',
            ]"
          >
            <EmailArea
              v-if="activity.type === 'email'"
              :activity="activity"
              :show-split-option="!activity.isFirstEmail && ticketStatus !== 'Closed'"
              class="py-2 px-3"
              @reply="(e) => emit('email:reply', e)"
            />
            <CommentBox
              v-else-if="activity.type === 'comment'"
              :activity="activity"
              @update="() => emit('update')"
            />
            <!-- TASK -->
            <div v-else-if="activity.type === 'task'" class="flex-1">
              <Taskbox
                :activity="activity"
                :reload-tasks="() => emit('update')"
                @update="() => emit('update')"
              />
            </div>
            <HistoryBox v-else-if="activity.type === 'call'" :activity="activity" />
            <FeedbackBox v-else-if="activity.type === 'feedback'" :activity="activity" />
            <HistoryBox v-else :activity="activity" />
          </div>
        </div>
      </div>
    </div>

    <div
      v-else
      class="h-screen flex flex-col items-center justify-center gap-3 font-medium text-gray-500"
    >
      <component :is="emptyTextIcon" class="h-7.5 w-7.5" />
      <span class="text-lg font-medium text-ink-gray-8">{{ __(emptyText) }}</span>
    </div>
  </FadedScrollableDiv>
</template>

<script setup lang="ts">
import { computed, h, inject, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Avatar, FeatherIcon } from 'frappe-ui'
import { FadedScrollableDiv } from '@/components'
import { ActivityIcon, CommentIcon, DotIcon, EmailIcon, PhoneIcon ,TaskIcon} from '@/components/icons'
import { useUserStore } from '@/stores/user'
import { TicketActivity } from '@/types'
import { isElementInViewport } from '@/utils'
import { __ } from '@/translation'
import FeedbackBox from '../ticket-agent/FeedbackBox.vue'
import CommentBox from '@/components/CommentBox.vue'
import EmailArea from '@/components/EmailArea.vue'
import HistoryBox from '@/components/HistoryBox.vue'
import Taskbox from '@/components/Taskbox.vue'
import TaskboxEditor from '@/components/TaskboxEditor.vue'

const props = defineProps({
  activities: {
    type: Array as () => TicketActivity[],
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  ticketStatus: {
    type: String,
    default: '',
  },
  ticketId: {
    type: [String, Number],
    default: '',
  },
})

const emit = defineEmits(['email:reply', 'update', 'new-email'])

const route = useRoute()
const router = useRouter()
const { getUser } = useUserStore()

const showNewTaskModal = ref(false)

// Prefer the prop; fall back to inject for backward-compat with older callers
const injectedTicketId = inject<string | number>('ticketId', '')
const resolvedTicketId = computed(() =>
  String(props.ticketId || injectedTicketId || '').trim()
)

const localActivities = ref([...props.activities])
watch(
  () => props.activities,
  (val) => { localActivities.value = [...val] },
  { immediate: true, deep: true },
)

const emptyText = computed(() => {
  if (props.title === __('Emails'))   return 'No email communications'
  if (props.title === __('Comments')) return 'No comments found'
  if (props.title === __('Calls'))    return 'No calls made'
  if (props.title === __('Tasks'))    return 'No tasks found'
  return 'No activity found'
})

const emptyTextIcon = computed(() => {
  let icon: any = ActivityIcon
  if (props.title === __('Emails'))        icon = EmailIcon
  else if (props.title === __('Comments')) icon = CommentIcon
  else if (props.title === __('Calls'))    icon = PhoneIcon
  else if (props.title === __('Tasks'))    icon = TaskIcon
  return h(icon, { class: 'text-gray-500' })
})

onMounted(() => { nextTick(() => { document.querySelector('.activity')?.focus() }) })

function scrollToLatestActivity() {
  if (route.hash) { scrollToHash(); return }
  setTimeout(() => {
    const elements = document.getElementsByClassName('activity')
    const el = elements[elements.length - 1] as HTMLElement
    if (el && !isElementInViewport(el)) {
      ;(el as any).scrollIntoViewIfNeeded()
      el.focus()
    }
  }, 500)
}

function scrollToHash() {
  const hash = route.hash
  if (!hash) return
  nextTick(() => {
    setTimeout(() => {
      const element = document.getElementById(hash.substring(1))
      if (element) {
        ;(element as any).scrollIntoViewIfNeeded()
        element.classList.add('bg-yellow-100')
        setTimeout(() => {
          element.classList.remove('bg-yellow-100')
          router.replace({ hash: '' })
        }, 2000)
      }
    }, 1000)
  })
}

watch(() => route.hash, scrollToLatestActivity)
watch(() => props.title, scrollToLatestActivity, { immediate: true })

defineExpose({ scrollToLatestActivity })
</script>

<style scoped>
.activity:focus { outline: none; }
</style>