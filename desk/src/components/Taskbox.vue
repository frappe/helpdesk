<template>
  <div class="w-full">
    <div
      class="activity flex cursor-pointer items-start justify-between gap-4 px-4 py-3 rounded-xl hover:bg-surface-gray-1 transition-colors duration-200 w-full"
      @click="showModal = true"
    >
      <div class="flex flex-1 flex-col gap-2 min-w-0">
        <div class="truncate text-sm font-medium text-ink-gray-9">
          {{ activity.title || __('Untitled Task') }}
        </div>

        <div class="flex flex-wrap items-center gap-1.5 text-[13px] text-[#383838]">
          <div v-if="assignedId" class="flex items-center gap-1.5">
            <Avatar
              shape="circle"
              size="xs"
              :label="userInfo.full_name || assigneeLabel"
              :image="userInfo.user_image || ''"
            />
            <span>{{ userInfo.full_name || assigneeLabel }}</span>
          </div>

          <div v-if="assignedId && activity.due_date" class="flex items-center justify-center">
            <DotIcon class="h-1.5 w-1.5 text-ink-gray-4" />
          </div>

          <Tooltip
            v-if="activity.due_date"
            :text="dateFormat(activity.due_date, dateTooltipFormat)"
          >
            <div class="flex items-center gap-1.5">
              <CalendarIcon class="h-3.5 w-3.5 text-ink-gray-5" />
              <span>{{ dateFormat(activity.due_date, 'D MMM, h:mm A') }}</span>
            </div>
          </Tooltip>

          <div
            v-if="(assignedId || activity.due_date) && activity.priority"
            class="flex items-center justify-center"
          >
            <DotIcon class="h-1.5 w-1.5 text-ink-gray-4" />
          </div>

          <div v-if="activity.priority" class="flex items-center">
            <span>{{ activity.priority }}</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-1 shrink-0" @click.stop>
        <Dropdown :options="statusDropdownOptions" placement="bottom-end">
          <Button
            :tooltip="__('Change Status')"
            variant="ghost"
            class="text-ink-gray-8 hover:bg-surface-gray-3 hover:text-ink-gray-9"
            :disabled="isUpdating"
          >
            <TaskStatusIcon :status="activity.status || 'Todo'" class="h-4 w-4" />
          </Button>
        </Dropdown>

        <!-- Custom controlled popover -->
        <div class="relative" ref="menuWrapperRef">
          <button
            class="flex h-7 w-7 items-center justify-center rounded-md text-ink-gray-8 hover:bg-surface-gray-3 hover:text-ink-gray-9 transition-colors"
            @click="toggleMenu"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="5" cy="12" r="2"/>
              <circle cx="12" cy="12" r="2"/>
              <circle cx="19" cy="12" r="2"/>
            </svg>
          </button>

          <Transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="opacity-100 scale-100"
            leave-to-class="opacity-0 scale-95"
          >
            <div
              v-if="menuOpen"
              class="absolute right-0 z-50 mt-1 min-w-[160px] origin-top-right rounded-xl border border-surface-gray-2 bg-white shadow-xl py-1.5"
            >
              <button
                class="flex w-full items-center gap-2.5 px-3 py-1.5 text-left text-sm transition-colors duration-150 rounded-lg"
                :class="isConfirmingDelete
                  ? 'text-red-500 font-medium hover:bg-red-50'
                  : 'text-ink-gray-7 hover:bg-surface-gray-1'"
                style="width: calc(100% - 8px); margin: 0 4px;"
                @click="deleteTask"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-4 w-4 shrink-0"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6l-1 14H6L5 6" />
                  <path d="M10 11v6" />
                  <path d="M14 11v6" />
                  <path d="M9 6V4h6v2" />
                </svg>
                {{ isConfirmingDelete ? __('Confirm Delete') : __('Delete') }}
              </button>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <div class="mx-3 border-b border-surface-gray-1" />

    <TaskboxEditor
      v-if="showModal"
      v-model="showModal"
      :task="activity"
      :ticketId="String(activity.reference_docname || '')"
      @submit="handleReload"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { Avatar, Button, Dropdown, Tooltip, call, toast } from 'frappe-ui'
import { dateTooltipFormat, dateFormat } from '@/utils'
import { __ } from '@/translation'
import { useUserStore } from '@/stores/user'
import CalendarIcon   from '@/components/icons/CalendarIcon.vue'
import DotIcon        from '@/components/icons/DotIcon.vue'
import TaskStatusIcon from '@/components/icons/TaskStatusIcon.vue'
import TaskboxEditor  from './TaskboxEditor.vue'

const props = defineProps({
  activity: {
    type:     Object,
    required: true,
  },
  reloadTasks: {
    type:    Function,
    default: null,
  },
  i: {
    type:    Number,
    default: 0,
  },
  tasks: {
    type:    Array,
    default: () => [],
  },
})

const emit = defineEmits(['update', 'status-change', 'deleted'])

const showModal          = ref(false)
const isUpdating         = ref(false)
const isConfirmingDelete = ref(false)
const menuOpen           = ref(false)
const menuWrapperRef     = ref<HTMLElement | null>(null)
const { getUser }        = useUserStore()

function toggleMenu() {
  menuOpen.value = !menuOpen.value
  if (!menuOpen.value) {
    isConfirmingDelete.value = false
  }
}

function handleOutsideClick(e: MouseEvent) {
  if (menuWrapperRef.value && !menuWrapperRef.value.contains(e.target as Node)) {
    menuOpen.value           = false
    isConfirmingDelete.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleOutsideClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleOutsideClick)
})

const assignedId = computed(() =>
  props.activity.assigned || props.activity.assigned_to || ''
)

const userInfo = computed(() => {
  const email = assignedId.value
  if (!email) return { full_name: '', user_image: '' }
  return getUser(email) || { full_name: '', user_image: '' }
})

const assigneeLabel = computed((): string => {
  const assigned = assignedId.value
  if (!assigned) return ''
  return assigned
})

async function changeStatus(newStatus: string) {
  if (isUpdating.value) return

  const taskId = props.activity.name || props.activity.id
  if (!taskId) {
    toast.error(__('Could not resolve Task ID.'))
    return
  }

  isUpdating.value = true

  const previousStatus     = props.activity.status
  props.activity.status    = newStatus

  try {
    await call('helpdesk.helpdesk.doctype.hd_task.hd_task.update_task', {
      task:   taskId,
      status: newStatus,
    })
    emit('status-change', { name: taskId, status: newStatus })
    emit('update')
    props.reloadTasks?.()
  } catch (e: any) {
    props.activity.status = previousStatus
    toast.error(e?.message || __('Failed to update status'))
  } finally {
    isUpdating.value = false
  }
}

async function deleteTask() {
  if (isUpdating.value) return

  // First click: toggle label, keep menu open
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }

  // Second click: actually delete
  const taskId = props.activity.name || props.activity.id
  if (!taskId) {
    toast.error(__('Task identifier missing, cannot delete.'))
    isConfirmingDelete.value = false
    menuOpen.value           = false
    return
  }

  isUpdating.value = true
  emit('deleted', taskId)

  try {
    await call('helpdesk.helpdesk.doctype.hd_task.hd_task.delete_task', {
      task: taskId,
    })
    toast.success(__('Task deleted successfully'))
    emit('update')
    props.reloadTasks?.()
  } catch (e: any) {
    emit('update')
    toast.error(e?.message || __('Failed to delete task'))
  } finally {
    isUpdating.value         = false
    isConfirmingDelete.value = false
    menuOpen.value           = false
  }
}

const statusDropdownOptions = computed(() =>
  [
    { label: __('Backlog'),     value: 'Backlog'     },
    { label: __('Todo'),        value: 'Todo'        },
    { label: __('In Progress'), value: 'In Progress' },
    { label: __('Done'),        value: 'Done'        },
    { label: __('Canceled'),    value: 'Canceled'    },
  ].map((s) => ({
    label:   s.label,
    value:   s.value,
    onClick: () => changeStatus(s.value),
  }))
)

function handleReload(payload?: any) {
  showModal.value = false

  const data = payload?.message || payload

  if (data && typeof data === 'object') {
    Object.keys(data).forEach(key => {
      if (key in props.activity) {
        props.activity[key] = data[key]
      }
    })
    if (data.assigned)  props.activity.assigned  = data.assigned
    if (data.title)     props.activity.title     = data.title
    if (data.due_date)  props.activity.due_date  = data.due_date
    if (data.priority)  props.activity.priority  = data.priority
    if (data.status)    props.activity.status    = data.status
  }

  emit('update')

  if (props.reloadTasks) {
    props.reloadTasks()
  }
}
</script>
