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

app.mount("#app")
