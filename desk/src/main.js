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
	updateContact: (contactId) => {},
	createContact: (emailId, fullName) => {},

	createType: (type) => {},

	ticketFilter: "All Tickets",
	contactFilter: "All Contacts",

	currentPage: "Tickets"	// Tickets, Ticket, Contacts, ...
})

app.config.globalProperties.$ticketFilter = {
	set(newValue) { 
		globalVariables.value.ticketFilter= newValue;
	},
	get() {
		return globalVariables.value.ticketFilter;
	}
};

app.config.globalProperties.$contactFilter = {
	set(newValue) { 
		globalVariables.value.contactFilter= newValue;
	},
	get() {
		return globalVariables.value.contactFilter;
	}
};

app.config.globalProperties.$currentPage = {
	set(newValue) { 
		globalVariables.value.currentPage= newValue;
	},
	get() {
		return globalVariables.value.currentPage;
	}
};

app.mount('#app')
