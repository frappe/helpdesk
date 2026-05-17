<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ isEditing ? __('Edit Task') : __('Create Task') }}
        </h3>
      </div>
    </template>

    <template #body-content>
      <div class="flex flex-col gap-4">

        <div class="space-y-1.5">
          <FormLabel :label="__('Title')" required />
          <TextInput
            ref="titleRef"
            v-model="form.title"
            :placeholder="__('Enter task title')"
          />
        </div>

        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">
            {{ __('Description') }}
          </div>
          <TextEditor
            variant="outline"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2]"
            :bubbleMenu="true"
            :content="form.description"
            :placeholder="__('Task description')"
            @change="(val) => (form.description = val)"
          />
        </div>

        <div class="flex flex-wrap items-center gap-2">

          <Dropdown :options="statusDropdownOptions">
            <Button :label="form.status">
              <template #prefix>
                <TaskStatusIcon :status="form.status" />
              </template>
            </Button>
          </Dropdown>

          <Autocomplete
            v-model="selectedAssignee"
            :options="agentOptions"
            :placeholder="__('Assign To')"
          >
            <template #prefix>
              <Avatar
                v-if="form.assigned_to"
                class="mr-2 !h-4 !w-4"
                shape="circle"
                :label="form.assigned_to"
              />
              <FeatherIcon v-else name="user" class="mr-2 h-4 w-4 text-ink-gray-4" />
            </template>
            <template #item-prefix="{ option }">
              <Avatar class="mr-2" shape="circle" :label="option.label" size="sm" />
            </template>
          </Autocomplete>

          <div class="w-40">
            <DateTimePicker
              v-model="form.due_date"
              class="datepicker"
              format="dd/MM/yyyy HH:mm"
              input-class="border-none"
            />
          </div>

          <Dropdown :options="priorityDropdownOptions">
            <Button :label="form.priority">
              <template #prefix>
                <TaskPriorityIcon :priority="form.priority" />
              </template>
            </Button>
          </Dropdown>

        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end">
        <Button
          :label="isEditing ? __('Update') : __('Create')"
          variant="solid"
          :loading="loading"
          :disabled="!form.title?.trim() || loading"
          @click="handleSubmit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import {
  Autocomplete,
  Avatar,
  Button,
  DateTimePicker,
  Dialog,
  Dropdown,
  FeatherIcon,
  FormLabel,
  TextEditor,
  TextInput,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { __ } from '@/translation'
import { isContentEmpty } from '@/utils'
import TaskStatusIcon from '@/components/icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/icons/TaskPriorityIcon.vue'

const props = defineProps({
  task: {
    type: Object,
    default: null,
  },
  ticketId: {
    type: [String, Number],
    default: '',
  },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['submit'])

const loading = ref(false)
const titleRef = ref(null)

const isEditing = computed(() => !!props.task?.name)

const defaultForm = () => ({
  title: '',
  description: '',
  due_date: '',
  status: 'Backlog',
  priority: 'Low',
  assigned_to: '',
})

const form = ref(defaultForm())

// Explicitly track the selected object to satisfy Autocomplete internal state structure
const selectedAssignee = ref<any>(null)

// 1. Fetch system users directly matching linked User DocType options setup
const usersList = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'User',
    fields: ['name', 'full_name', 'user_image'],
    filters: { 
      enabled: 1,
      user_type: 'System User'
    },
    page_length: 200,
  },
  auto: true,
})

// 2. Compute dropdown options map layout
const agentOptions = computed(() => {
  if (!usersList.data) return []
  return usersList.data.map((user: any) => ({
    label: user.full_name || user.name,
    value: user.name,
  }))
})

// Synchronize our view tracking object with our underlying string field model
watch(selectedAssignee, (newVal) => {
  if (!newVal) {
    form.value.assigned_to = ''
  } else if (typeof newVal === 'object') {
    form.value.assigned_to = newVal.value || ''
  } else {
    form.value.assigned_to = newVal
  }
})

watch(
  () => props.task,
  (task) => {
    if (task) {
      form.value = {
        title: task.title || '',
        description: task.description || '',
        due_date: task.due_date || '',
        status: task.status || 'Backlog',
        priority: task.priority || 'Low',
        assigned_to: task.assigned_to || '',
      }
      
      // Auto-populate active selection object layout when opening existing records
      if (task.assigned_to) {
        selectedAssignee.value = {
          label: task.assigned_to.split('@')[0],
          value: task.assigned_to
        }
      } else {
        selectedAssignee.value = null
      }
    } else {
      form.value = defaultForm()
      selectedAssignee.value = null
    }
  },
  { immediate: true },
)

watch(show, (val) => {
  if (val) {
    if (!props.task) {
      form.value = defaultForm()
      selectedAssignee.value = null
    }
    nextTick(() => setTimeout(() => titleRef.value?.el?.focus?.(), 100))
  }
})

const statusDropdownOptions = computed(() => [
  { label: __('Backlog'),     onClick: () => (form.value.status = 'Backlog') },
  { label: __('Todo'),        onClick: () => (form.value.status = 'Todo') },
  { label: __('In Progress'), onClick: () => (form.value.status = 'In Progress') },
  { label: __('Done'),        onClick: () => (form.value.status = 'Done') },
  { label: __('Canceled'),    onClick: () => (form.value.status = 'Canceled') },
])

const priorityDropdownOptions = computed(() => [
  { label: __('Low'),    onClick: () => (form.value.priority = 'Low') },
  { label: __('Medium'), onClick: () => (form.value.priority = 'Medium') },
  { label: __('High'),   onClick: () => (form.value.priority = 'High') },
])

async function handleSubmit() {
  if (!form.value.title?.trim()) {
    toast.error(__('Title is required'))
    return
  }
  if (loading.value) return
  loading.value = true

  try {
    let result: any

    if (isEditing.value) {
      result = await call(
        'helpdesk.helpdesk.doctype.hd_task.hd_task.update_task',
        {
          task: props.task.name,
          title: form.value.title,
          description: isContentEmpty(form.value.description) ? null : form.value.description,
          due_date: form.value.due_date || null,
          status: form.value.status,
          priority: form.value.priority,
          assigned_to: form.value.assigned_to || null,
        },
      )
      toast.success(__('Task updated'))
    } else {
      const ticketId = String(props.ticketId || '').trim()
      if (!ticketId) {
        toast.error(__('Ticket ID is missing'))
        return
      }
      result = await call(
        'helpdesk.helpdesk.doctype.hd_task.hd_task.create_task',
        {
          ticket: ticketId,
          title: form.value.title,
          description: isContentEmpty(form.value.description) ? null : form.value.description,
          due_date: form.value.due_date || null,
          status: form.value.status,
          priority: form.value.priority,
          assigned_to: form.value.assigned_to || null,
        },
      )
      toast.success(__('Task created'))
    }

    emit('submit', result)
    show.value = false
  } catch (e: any) {
    toast.error(e?.message || __('Something went wrong'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
:deep(.datepicker svg) {
  width: 0.875rem;
  height: 0.875rem;
}
</style>