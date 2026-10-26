import { computed, type Ref } from 'vue'
import { dayjsLocal } from '@helpdesk/shared/timezone'
import { __ } from '@helpdesk/shared/translation'

type Activity = { type?: string; key?: string; timestamp: string; data?: any; author?: any; icon?: any }

export type ChatRow =
  | { kind: 'day'; key: string; label: string }
  | { kind: 'event'; key: string; activity: Activity }
  // Customers on the right, agents on the left; the viewer's own go unnamed.
  | { kind: 'message'; key: string; activity: Activity; isCustomer: boolean; isViewer: boolean }

// The only structure is a rule between calendar days; messages never group.
export function useChatRows(
  activities: Ref<Activity[]>,
  { isCustomer, isViewer }: { isCustomer: (activity: Activity) => boolean; isViewer: (activity: Activity) => boolean },
) {
  return computed(() => {
    const rows: ChatRow[] = []
    let previousDay = ''
    for (const activity of activities.value) {
      const at = dayjsLocal(activity.timestamp)
      const day = at.format('YYYY-MM-DD')
      // No rule above the first day: nothing to separate yet.
      if (day !== previousDay) {
        if (previousDay) rows.push({ kind: 'day', key: `day:${day}`, label: dayLabel(at) })
        previousDay = day
      }
      const key = activity.key ?? `${activity.type}:${activity.data?.name ?? activity.timestamp}`
      rows.push(
        activity.type === 'email'
          ? { kind: 'message', key, activity, isCustomer: isCustomer(activity), isViewer: isViewer(activity) }
          : { kind: 'event', key, activity },
      )
    }
    return rows
  })
}

function dayLabel(at: ReturnType<typeof dayjsLocal>) {
  const today = dayjsLocal()
  if (at.isSame(today, 'day')) return __('Today')
  if (at.isSame(today.subtract(1, 'day'), 'day')) return __('Yesterday')
  return at.format(at.isSame(today, 'year') ? 'D MMMM' : 'D MMMM YYYY')
}
