import { createApp } from 'vue'
import { FrappeUI, Button, onOutsideClickDirective } from 'frappe-ui'
import router from './router'
import App from './App.vue'
import './index.css'
import { dayjs } from '@/utils'
import { createToast, clearToasts } from '@/utils/toasts'

let app = createApp(App)

app.directive('on-outside-click', onOutsideClickDirective)
app.use(router)
app.use(FrappeUI)
app.component('Button', Button)

app.config.globalProperties.$dayjs = dayjs
app.config.globalProperties.$toast = createToast
app.config.globalProperties.$clearToasts = clearToasts

app.mount('#app')
