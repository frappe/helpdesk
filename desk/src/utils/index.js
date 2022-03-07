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
		m: "1 minute",
		mm: "%d minutes",
		h: "1 hour",
		hh: "%d hours",
		d: "1 day",
		dd: "%d days",
		M: "1 month",
		MM: "%d months",
		y: "1 year",
		yy: "%d years"
	}
})

_dayjs.shortFormating = (s) => {
    if (s === 'Now') { 
        return s
    }

    const prefix = s.split(' ')[0]
    const posfix = s.split(' ')[1]
    let newPostfix = ''
    switch(posfix) {
        case 'second':
            newPostfix = 's'
            break
        case 'seconds':
            newPostfix = 's'
            break
        case 'minute':
            newPostfix = 'm'
            break
        case 'minutes':
            newPostfix = 'm'
            break
        case 'hour':
            newPostfix = 'h'
            break
        case 'hours':
            newPostfix = 'h'
            break
        case 'day':
            newPostfix = 'd'
            break
        case 'days':
            newPostfix = 'd'
            break
        case 'month':
            newPostfix = 'M'
            break
        case 'months':
            newPostfix = 'M'
            break
        case 'year':
            newPostfix = 'Y'
            break
        case 'years':
            newPostfix = 'Y'
            break
    }
    return `${prefix}${newPostfix}`
}

export let dayjs = _dayjs