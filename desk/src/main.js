import { createApp, ref } from 'vue'
import { FrappeUI, Button } from 'frappe-ui'
import router from './router'
import App from './App.vue'
import './index.css'
import { dayjs } from '@/utils'

let app = createApp(App)
app.use(router)
app.use(FrappeUI)
app.component('Button', Button)

app.config.globalProperties.$dayjs = dayjs

const globalVariables = ref({
	currentPage: "Tickets",	// Tickets, Ticket, Contacts, ...
	breadcrumbs: []
})

app.config.globalProperties.$currentPage = {
	set(newValue, breadcrumbs) { 
		globalVariables.value.breadcrumbs = breadcrumbs ? breadcrumbs : []
		globalVariables.value.currentPage = newValue;
	},
	get() {
		return globalVariables.value.currentPage;
	},
	breadcrumbs() {
		return globalVariables.value.breadcrumbs;
	}
};

app.mount('#app')
