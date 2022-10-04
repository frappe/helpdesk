// $event.emit('event-name') // emit event
// $event.on('event-name', callback) // listen event
// $event.off('event-name', callback) // remove listener

class Listener {
	constructor(event, callback) {
		this.event = event
		this.callback = callback
	}
}

const eventListeners = []

const createListener = (event, callback) => {
	eventListeners.push(new Listener(event, callback))
}

const removeListener = (event, callback) => {
	eventListeners.forEach((listener, index) => {
		if (listener.event === event && listener.callback === callback) {
			eventListeners.splice(index, 1)
		}
	})
}

const emit = (event, data) => {
	eventListeners.forEach((listener) => {
		if (listener.event === event) {
			listener.callback(data)
		}
	})
}

const event = {
	on: createListener,
	off: removeListener,
	emit: emit,
}

export { event }
