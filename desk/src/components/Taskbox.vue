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

        <Dropdown :options="dropdownOptions" placement="bottom-end">
          <Button
            icon="more-horizontal"
            variant="ghost"
            class="text-ink-gray-8 hover:bg-surface-gray-3 hover:text-ink-gray-9"
          />
        </Dropdown>
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
import { computed, ref } from 'vue'
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

const showModal  = ref(false)
const isUpdating = ref(false)
const { getUser } = useUserStore()

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

  // Optimistic UI update
  const previousStatus = props.activity.status
  props.activity.status = newStatus

  try {
    await call('helpdesk.helpdesk.doctype.hd_task.hd_task.update_task', {
      task:   taskId,
      status: newStatus,
    })
    emit('status-change', { name: taskId, status: newStatus })
    emit('update')
    props.reloadTasks?.()
  } catch (e: any) {
    props.activity.status = previousStatus // Fallback logic execution
    toast.error(e?.message || __('Failed to update status'))
  } finally {
    isUpdating.value = false
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

// ── Decoupled Async Delete Stream ─────────────────────────────────────────────
async function deleteTask() {
  if (isUpdating.value) return

  const taskId = props.activity.name || props.activity.id
  if (!taskId) {
    toast.error(__('Task identifier missing, cannot delete.'))
    return
  }

  isUpdating.value = true

  // Optimistic event emit to hide row from UI loop instantly
  emit('deleted', taskId)

  try {
    await call('helpdesk.helpdesk.doctype.hd_task.hd_task.delete_task', {
      task: taskId,
    })
    toast.success(__('Task deleted successfully'))
    emit('update')
    props.reloadTasks?.()
  } catch (e: any) {
    // Force array restore trigger up to container component layer on failure
    emit('update')
    toast.error(e?.message || __('Failed to delete task'))
  } finally {
    isUpdating.value = false
  }
}

const dropdownOptions = computed(() => [
  {
    label:   __('Delete'),
    icon:    'trash-2',
    onClick: deleteTask,
  },
])

function handleReload(payload?: any) {
  showModal.value = false

  const data = payload?.message || payload;
  
  if (data && typeof data === 'object') {
    Object.keys(data).forEach(key => {
        if (key in props.activity) {
            props.activity[key] = data[key];
        }
    });
    if (data.assigned) props.activity.assigned = data.assigned;
    if (data.title) props.activity.title = data.title;
    if (data.due_date) props.activity.due_date = data.due_date;
    if (data.priority) props.activity.priority = data.priority;
    if (data.status) props.activity.status = data.status;
  }
}
  

  emit('update')
  
  if (props.reloadTasks) {
    props.reloadTasks()
  }
</script>
