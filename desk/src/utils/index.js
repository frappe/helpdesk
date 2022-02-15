import _dayjs from 'dayjs'
import relativeTime from 'dayjs/esm/plugin/relativeTime'
_dayjs.extend(relativeTime)

export let dayjs = _dayjs