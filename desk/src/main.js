import { createApp } from "vue"
import {
	FrappeUI,
	Button,
	Dialog,
	Input,
	onOutsideClickDirective,
	Tooltip,
} from "frappe-ui"
import router from "./router"
import App from "./App.vue"
import "./index.css"
import { dayjs } from "@/utils"
import { createToast, clearToasts } from "@/utils/toasts"
import { event } from "@/utils/event"
import { socketio_port } from "../../../../sites/common_site_config.json"
import { tickets } from "@/controllers/tickets"
import { agents } from "@/controllers/agents"
import { contacts } from "@/controllers/contacts"
import { fdSettings } from "@/controllers/fdSettings"

let app = createApp(App)

app.directive("on-outside-click", onOutsideClickDirective)
app.use(router)
app.use(FrappeUI, {
	socketio: {
		port: socketio_port,
	},
})

app.component("Button", Button)
app.component("Dialog", Dialog)
app.component("Input", Input)
app.component("Tooltip", Tooltip)

app.config.unwrapInjectedRef = true

app.config.globalProperties.$dayjs = dayjs
app.config.globalProperties.$toast = createToast
app.config.globalProperties.$clearToasts = clearToasts
app.config.globalProperties.$event = event

app.config.globalProperties.$tickets = tickets
app.provide("$tickets", app.config.globalProperties.$tickets)

app.config.globalProperties.$agents = agents
app.provide("$agents", app.config.globalProperties.$agents)

app.config.globalProperties.$contacts = contacts
app.provide("$contacts", app.config.globalProperties.$contacts)

app.config.globalProperties.$fdSettings = fdSettings
app.provide("$fdSettings", app.config.globalProperties.$fdSettings)

app.provide("$socket", app.config.globalProperties.$socket)

app.mount("#app")
