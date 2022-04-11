import { createApp } from 'vue'
import { FrappeUI, Button, onOutsideClickDirective } from 'frappe-ui'
import router from './router'
import App from './App.vue'
import './index.css'
import { dayjs } from '@/utils'

let app = createApp(App)

app.directive('on-outside-click', onOutsideClickDirective)
app.use(router)
app.use(FrappeUI)
app.component('Button', Button)
app.directive('on-outside-click', onOutsideClickDirective)

app.config.globalProperties.$dayjs = dayjs

app.mount('#app')
