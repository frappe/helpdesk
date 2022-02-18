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

const user = ref();

app.config.globalProperties.$user = {
	set(userDetails) {
		user.value = userDetails;
	},
	get() {
		return user.value;
	}
};

const ticketFilter = ref('All Tickets');
app.config.globalProperties.$ticketFilter = {
	set(newValue) { 
		ticketFilter.value = newValue;
	},
	get() {
		return ticketFilter.value;
	}
};

app.mount('#app')
