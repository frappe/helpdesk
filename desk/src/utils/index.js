import _dayjs from 'dayjs'
import relativeTime from 'dayjs/esm/plugin/relativeTime'
import updateLocale from 'dayjs/esm/plugin/updateLocale'

_dayjs.extend(relativeTime)
_dayjs.extend(updateLocale)

_dayjs.updateLocale('en', {
  relativeTime: {
    future: "in %s",
    past: "%s",
    s: 'Now',
    m: "1m",
    mm: "%dm",
    h: "1h",
    hh: "%dh",
    d: "1d",
    dd: "%dd",
    M: "1M",
    MM: "%dM",
    y: "1y",
    yy: "%dy"
  }
})

export let dayjs = _dayjs