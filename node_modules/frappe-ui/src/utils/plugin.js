import resources from './resources'
import call from './call'
import socket from './socketio'

let defaultOptions = {
  resources: true,
  call: true,
  socketio: true,
}

export default {
  install(app, options = {}) {
    options = Object.assign({}, defaultOptions, options)
    options.resources && app.use(resources, options.resources)

    if (options.call) {
      let callFunction = typeof options.call == 'function' ? options.call : call
      app.config.globalProperties.$call = callFunction
    }
    if (options.socketio) {
      app.config.globalProperties.$socket = socket
    }
  },
}
