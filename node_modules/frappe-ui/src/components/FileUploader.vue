<template>
  <div>
    <input
      ref="input"
      type="file"
      :accept="fileTypes"
      class="hidden"
      @change="onFileAdd"
    />
    <slot
      v-bind="{
        file,
        uploading,
        progress,
        uploaded,
        message,
        error,
        total,
        success,
        openFileSelector,
      }"
    />
  </div>
</template>

<script>
class FileUploader {
  constructor() {
    this.listeners = {}
  }

  on(event, handler) {
    this.listeners[event] = this.listeners[event] || []
    this.listeners[event].push(handler)
  }

  trigger(event, data) {
    let handlers = this.listeners[event] || []
    handlers.forEach((handler) => {
      handler.call(this, data)
    })
  }

  upload(file, options) {
    return new Promise((resolve, reject) => {
      let xhr = new XMLHttpRequest()
      xhr.upload.addEventListener('loadstart', () => {
        this.trigger('start')
      })
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          this.trigger('progress', {
            uploaded: e.loaded,
            total: e.total,
          })
        }
      })
      xhr.upload.addEventListener('load', () => {
        this.trigger('finish')
      })
      xhr.addEventListener('error', () => {
        this.trigger('error')
        reject()
      })
      xhr.onreadystatechange = () => {
        if (xhr.readyState == XMLHttpRequest.DONE) {
          let error
          if (xhr.status === 200) {
            let r = null
            try {
              r = JSON.parse(xhr.responseText)
            } catch (e) {
              r = xhr.responseText
            }
            let out = r.message || r
            resolve(out)
          } else if (xhr.status === 403) {
            error = JSON.parse(xhr.responseText)
          } else {
            this.failed = true
            try {
              error = JSON.parse(xhr.responseText)
            } catch (e) {
              // pass
            }
          }
          if (error && error.exc) {
            console.error(JSON.parse(error.exc)[0])
          }
          reject(error)
        }
      }
      xhr.open('POST', '/api/method/upload_file', true)
      xhr.setRequestHeader('Accept', 'application/json')
      if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') {
        xhr.setRequestHeader('X-Frappe-CSRF-Token', window.csrf_token)
      }

      let form_data = new FormData()
      if (file) {
        form_data.append('file', file, file.name)
      }
      form_data.append('is_private', +(options.private || 0))
      form_data.append('folder', options.folder || 'Home')

      if (options.file_url) {
        form_data.append('file_url', options.file_url)
      }

      if (options.doctype && options.docname) {
        form_data.append('doctype', options.doctype)
        form_data.append('docname', options.docname)
        if (options.fieldname) {
          form_data.append('fieldname', options.fieldname)
        }
      }

      if (options.method) {
        form_data.append('method', options.method)
      }

      if (options.type) {
        form_data.append('type', options.type)
      }

      xhr.send(form_data)
    })
  }
}

export default {
  name: 'FileUploader',
  props: ['fileTypes', 'uploadArgs', 'type', 'validateFile'],
  data() {
    return {
      uploader: null,
      uploading: false,
      uploaded: 0,
      error: null,
      message: '',
      total: 0,
      file: null,
      finishedUploading: false,
    }
  },
  computed: {
    progress() {
      let value = Math.floor((this.uploaded / this.total) * 100)
      return isNaN(value) ? 0 : value
    },
    success() {
      return this.finishedUploading && !this.error
    },
  },
  methods: {
    openFileSelector() {
      this.$refs['input'].click()
    },
    async onFileAdd(e) {
      this.error = null
      this.file = e.target.files[0]

      if (this.file && this.validateFile) {
        try {
          let message = await this.validateFile(this.file)
          if (message) {
            this.error = message
          }
        } catch (error) {
          this.error = error
        }
      }

      if (!this.error) {
        this.uploadFile(this.file)
      }
    },
    async uploadFile(file) {
      this.error = null
      this.uploaded = 0
      this.total = 0

      this.uploader = new FileUploader()
      this.uploader.on('start', () => {
        this.uploading = true
      })
      this.uploader.on('progress', (data) => {
        this.uploaded = data.uploaded
        this.total = data.total
      })
      this.uploader.on('error', () => {
        this.uploading = false
        this.error = 'Error Uploading File'
      })
      this.uploader.on('finish', () => {
        this.uploading = false
        this.finishedUploading = true
      })
      this.uploader
        .upload(file, this.uploadArgs || {})
        .then((data) => {
          this.$emit('success', data)
        })
        .catch((error) => {
          this.uploading = false
          let errorMessage = 'Error Uploading File'
          if (error._server_messages) {
            errorMessage = JSON.parse(
              JSON.parse(error._server_messages)[0]
            ).message
          } else if (error.exc) {
            errorMessage = JSON.parse(error.exc)[0].split('\n').slice(-2, -1)[0]
          }
          this.error = errorMessage
          this.$emit('failure', error)
        })
    },
  },
}
</script>
