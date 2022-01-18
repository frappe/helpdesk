import { createApp } from 'vue'
import { FrappeUI, Button } from 'frappe-ui'
import router from './router'
import App from './App.vue'
import './index.css'

let app = createApp(App)
app.use(router)
app.use(FrappeUI)
app.component('Button', Button)
app.mount('#app')
