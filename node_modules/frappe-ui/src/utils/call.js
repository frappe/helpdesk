export default async function call(method, args, options = {}) {
  if (!args) {
    args = {}
  }

  let headers = Object.assign(
    {
      Accept: 'application/json',
      'Content-Type': 'application/json; charset=utf-8',
      'X-Frappe-Site-Name': window.location.hostname,
    },
    options.headers || {}
  )

  if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') {
    headers['X-Frappe-CSRF-Token'] = window.csrf_token
  }

  let path = method.startsWith('/') ? method : `/api/method/${method}`
  const res = await fetch(path, {
    method: 'POST',
    headers,
    body: JSON.stringify(args),
  })

  if (res.ok) {
    const data = await res.json()
    if (data.docs || method === 'login') {
      return data
    }
    if (data.exc) {
      try {
        console.groupCollapsed(method)
        console.log(`method: ${method}`)
        console.log(`params:`, args)
        let warning = JSON.parse(data.exc)
        for (let text of warning) {
          console.log(text)
        }
        console.groupEnd()
      } catch (e) {
        console.warn('Error printing debug messages', e)
      }
    }
    return data.message
  } else {
    let response = await res.text()
    let error, exception
    try {
      error = JSON.parse(response)
      // eslint-disable-next-line no-empty
    } catch (e) {}
    let errorParts = [
      [method, error.exc_type, error._error_message].filter(Boolean).join(' '),
    ]
    if (error.exc) {
      exception = error.exc
      try {
        exception = JSON.parse(exception)[0]
        console.log(exception)
        // eslint-disable-next-line no-empty
      } catch (e) {}
    }
    let e = new Error(errorParts.join('\n'))
    e.exc_type = error.exc_type
    e.exc = exception
    e.status = res.status
    e.messages = error._server_messages
      ? JSON.parse(error._server_messages)
      : []
    e.messages = e.messages.concat(error.message)
    e.messages = e.messages.map((m) => {
      try {
        return JSON.parse(m).message
      } catch (error) {
        return m
      }
    })
    e.messages = e.messages.filter(Boolean)
    if (!e.messages.length) {
      e.messages = error._error_message
        ? [error._error_message]
        : ['Internal Server Error']
    }

    if (options.onError) {
      options.onError({ response: res, status: res.status, error: e })
    }

    throw e
  }
}

export function createCall(options) {
  return function customCall(method, args) {
    return call(method, args, options)
  }
}
