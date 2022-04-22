import _dayjs from 'dayjs'
import relativeTime from 'dayjs/esm/plugin/relativeTime'
import updateLocale from 'dayjs/esm/plugin/updateLocale'

_dayjs.extend(relativeTime)
_dayjs.extend(updateLocale)

_dayjs.updateLocale('en', {
	relativeTime: {
		future: "%s",
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
		y: "1Y",
		yy: "%dY"
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

export function remove_script_and_style(txt) {
    const evil_tags = ["script", "style", "noscript", "title", "meta", "base", "head"];
    const regex = new RegExp(evil_tags.map(tag => `<${tag}>.*<\\/${tag}>`).join('|'), 's');
    if (!regex.test(txt)) {
        // no evil tags found, skip the DOM method entirely!
        return txt;
    }

    var div = document.createElement('div');
    div.innerHTML = txt;
    var found = false;
    evil_tags.forEach(function(e) {
        var elements = div.getElementsByTagName(e);
        i = elements.length;
        while (i--) {
            found = true;
            elements[i].parentNode.removeChild(elements[i]);
        }
    });

    // remove links with rel="stylesheet"
    var elements = div.getElementsByTagName('link');
    var i = elements.length;
    while (i--) {
        if (elements[i].getAttribute("rel")=="stylesheet"){
            found = true;
            elements[i].parentNode.removeChild(elements[i]);
        }
    }
    if(found) {
        return div.innerHTML;
    } else {
        // don't disturb
        return txt;
    }
}

export let dayjs = _dayjs