import { call, debounce } from 'frappe-ui'
import { reactive, watch } from 'vue'

let cached = {}
let documentCache = reactive({})
let listCache = reactive({})

export function createResource(options, vm, getResource) {
  let cacheKey = null
  if (options.cache) {
    cacheKey = getCacheKey(options.cache)
    if (cached[cacheKey]) {
      return cached[cacheKey]
    }
  }

  if (typeof options == 'string') {
    options = {
      method: options,
      auto: true,
    }
  }

  let resourceFetcher = getResource || call
  let fetchFunction = options.debounce
    ? debounce(fetch, options.debounce)
    : fetch

  let out = reactive({
    data: options.initialData || null,
    previousData: null,
    loading: false,
    fetched: false,
    error: null,
    auto: options.auto,
    params: null,
    fetch: fetchFunction,
    reload: fetchFunction,
    submit: fetchFunction,
    reset,
    update,
    setData,
  })

  async function fetch(params, tempOptions = {}) {
    if (params instanceof Event) {
      params = null
    }
    params = params || out.params
    if (options.makeParams) {
      params = options.makeParams.call(vm, params)
    }
    out.params = params
    out.previousData = out.data ? JSON.parse(JSON.stringify(out.data)) : null
    out.loading = true

    if (options.onFetch) {
      options.onFetch.call(vm, out.params)
    }

    let validateFunction = tempOptions.validate || options.validate
    let errorFunctions = [options.onError, tempOptions.onError]
    let successFunctions = [options.onSuccess, tempOptions.onSuccess]

    if (validateFunction) {
      let invalidMessage
      try {
        invalidMessage = await validateFunction.call(vm, out.params)
        if (invalidMessage && typeof invalidMessage == 'string') {
          let error = new Error(invalidMessage)
          handleError(error, errorFunctions)
          out.loading = false
          return
        }
      } catch (error) {
        handleError(error, errorFunctions)
        out.loading = false
        return
      }
    }

    try {
      let data = await resourceFetcher(options.method, params || options.params)
      out.data = data
      out.fetched = true
      for (let fn of successFunctions) {
        if (fn) {
          fn.call(vm, data)
        }
      }
    } catch (error) {
      handleError(error, errorFunctions)
    }
    out.loading = false
  }

  function update({ method, params, auto }) {
    if (method && method !== options.method) {
      out.method = method
    }
    if (params && params !== options.params) {
      out.params = params
    }
    if (auto !== undefined && auto !== out.auto) {
      out.auto = auto
    }
  }

  function reset() {
    out.data = options.initialData || null
    out.previousData = null
    out.loading = false
    out.fetched = false
    out.error = null
    out.params = null
    out.auto = options.auto
  }

  function handleError(error, errorFunctions) {
    console.error(error)
    if (out.previousData) {
      out.data = out.previousData
    }
    out.error = error
    for (let fn of errorFunctions) {
      if (fn) {
        fn.call(vm, error)
      }
    }
  }

  // usage:
  // setData(newData) or
  // setData(data => data.filter(d => !d.deleted))
  function setData(data) {
    if (typeof data === 'function') {
      data = data.call(vm, out.data)
    }
    out.data = data
  }

  if (cacheKey && !cached[cacheKey]) {
    cached[cacheKey] = out
  }

  return out
}

export function createDocumentResource(options, vm) {
  if (!(options.doctype && options.name)) return

  let cacheKey = getCacheKey([options.doctype, options.name])
  if (documentCache[cacheKey]) {
    return documentCache[cacheKey]
  }

  let setValueOptions = {
    method: 'frappe.client.set_value',
    makeParams(values) {
      return {
        doctype: out.doctype,
        name: out.name,
        fieldname: values,
      }
    },
    onSuccess(data) {
      out.doc = transform(data)
    },
  }

  let out = reactive({
    doctype: options.doctype,
    name: options.name,
    doc: null,
    get: createResource(
      {
        method: 'frappe.client.get',
        makeParams() {
          return {
            doctype: out.doctype,
            name: out.name,
          }
        },
        onSuccess(data) {
          out.doc = transform(data)
        },
      },
      vm
    ),
    setValue: createResource(setValueOptions, vm),
    setValueDebounced: createResource(
      {
        ...setValueOptions,
        debounce: options.debounce || 500,
      },
      vm
    ),
    delete: createResource(
      {
        method: 'frappe.client.delete',
        makeParams() {
          return {
            doctype: out.doctype,
            name: out.name,
          }
        },
        onSuccess() {
          out.doc = null
        },
      },
      vm
    ),
    update,
    reload,
  })

  for (let method in options.whitelistedMethods) {
    let methodName = options.whitelistedMethods[method]
    out[method] = createResource(
      {
        method: 'run_doc_method',
        makeParams(values) {
          return {
            dt: out.doctype,
            dn: out.name,
            method: methodName,
            args: JSON.stringify(values),
          }
        },
        onSuccess(data) {
          if (data.docs) {
            for (let doc of data.docs) {
              if (doc.doctype === out.doctype && doc.name === out.name) {
                out.doc = transform(doc)
                break
              }
            }
          }
        },
      },
      vm
    )
  }

  function update(updatedOptions) {
    out.doctype = updatedOptions.doctype
    out.name = updatedOptions.name
    out.get.fetch()
  }

  function reload() {
    return out.get.fetch()
  }

  function transform(doc) {
    if (options.transform) {
      let returnValue = options.transform.call(vm, doc)
      if (typeof returnValue === 'object') {
        return returnValue
      }
    }
    return doc
  }

  // fetch the doc
  out.get.fetch()
  // cache
  documentCache[cacheKey] = out
  return out
}

function createListResource(options, vm, getResource) {
  if (!options.doctype) return

  let cacheKey = getCacheKey(options.cache)
  if (listCache[cacheKey]) {
    return listCache[cacheKey]
  }

  let out = reactive({
    doctype: options.doctype,
    fields: options.fields,
    filters: options.filters,
    order_by: options.order_by,
    start: options.start,
    limit: options.limit,
    data: null,
    list: createResource(
      {
        method: 'frappe.client.get_list',
        makeParams() {
          return {
            doctype: out.doctype,
            fields: out.fields,
            filters: out.filters,
            order_by: out.order_by,
            limit_start: out.start,
            limit_page_length: out.limit,
          }
        },
        onSuccess(data) {
          out.data = transform(data)
          options.onSuccess && options.onSuccess.call(vm, out.data)
        },
      },
      vm
    ),
    insert: createResource(
      {
        method: 'frappe.client.insert',
        makeParams(values) {
          return {
            doc: {
              doctype: out.doctype,
              ...values,
            },
          }
        },
        onSuccess() {
          out.list.fetch()
        },
      },
      vm
    ),
    setValue: createResource(
      {
        method: 'frappe.client.set_value',
        makeParams(options) {
          let { name, ...values } = options
          return {
            doctype: out.doctype,
            name: name,
            fieldname: values,
          }
        },
        onSuccess() {
          out.list.fetch()
        },
      },
      vm
    ),
    delete: createResource(
      {
        method: 'frappe.client.delete',
        makeParams(name) {
          return {
            doctype: out.doctype,
            name,
          }
        },
        onSuccess() {
          out.list.fetch()
        },
      },
      vm
    ),
    update,
    reload,
    setData,
  })

  function update(updatedOptions) {
    out.doctype = updatedOptions.doctype
    out.fields = updatedOptions.fields
    out.filters = updatedOptions.filters
    out.order_by = updatedOptions.order_by
    out.start = updatedOptions.start
    out.limit = updatedOptions.limit
    out.list.fetch()
  }

  function transform(data) {
    if (options.transform) {
      let returnValue = options.transform.call(vm, data)
      if (typeof returnValue != null) {
        return returnValue
      }
    }
    return data
  }

  function reload() {
    return out.list.fetch()
  }

  function setData(data) {
    if (typeof data === 'function') {
      data = data.call(vm, out.data)
    }
    out.data = data
  }

  // fetch list
  out.list.fetch()

  // cache
  listCache[cacheKey] = out

  return out
}

function createResourceForOptions(options, vm, getResource) {
  if (options.type === 'document') {
    return createDocumentResource(options, vm, getResource)
  }
  if (options.type === 'list') {
    return createListResource(options, vm, getResource)
  }
  return createResource(options, vm, getResource)
}

function getCacheKey(cacheKey) {
  if (typeof cacheKey === 'string') {
    cacheKey = [cacheKey]
  }
  return JSON.stringify(cacheKey)
}

let createMixin = (mixinOptions) => ({
  created() {
    if (this.$options.resources) {
      this._resources = reactive({})
      for (let key in this.$options.resources) {
        let options = this.$options.resources[key]

        if (typeof options == 'function') {
          watch(
            () => {
              try {
                return options.call(this)
              } catch (error) {
                console.warn('Failed to get resource options\n\n', error)
                return null
              }
            },
            (updatedOptions, oldVal) => {
              if (!updatedOptions) {
                return
              }

              let changed =
                !oldVal ||
                JSON.stringify(updatedOptions) !== JSON.stringify(oldVal)

              if (!changed) return

              let resource = this._resources[key]
              if (!resource) {
                resource = createResourceForOptions(
                  updatedOptions,
                  this,
                  mixinOptions.getResource
                )
                this._resources[key] = resource
              } else {
                resource.update(updatedOptions)
              }
              if (resource && resource.auto) {
                resource.fetch()
              }
            },
            {
              immediate: true,
            }
          )
        } else {
          let resource = createResourceForOptions(
            options,
            this,
            mixinOptions.getResource
          )
          this._resources[key] = resource
          if (resource.auto) {
            resource.fetch()
          }
        }
      }
    }
  },
  methods: {
    $getResource(cache) {
      let cacheKey = getCacheKey(cache)
      return cached[cacheKey] || null
    },
    $getDocumentResource(doctype, name) {
      let cacheKey = getCacheKey([doctype, name])
      return documentCache[cacheKey] || null
    },
    $getListResource(cache) {
      let cacheKey = getCacheKey(cache)
      return listCache[cacheKey] || null
    },
    $refetchResource(cache) {
      let resource = this.$getResource(cache)
      resource && resource.fetch()
    },
  },
  computed: {
    $resources() {
      return this._resources
    },
  },
})

export default {
  install(app, options) {
    let resourceMixin = createMixin(options)
    app.mixin(resourceMixin)
  },
}
