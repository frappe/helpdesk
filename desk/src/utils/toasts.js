import { h, reactive, ref } from 'vue'
import Toast from '@/components/global/Toast.vue'

let toasts = ref([])

export let Toasts = {
  name: 'Toasts',
  render() {
	return toasts.value.map((toast) =>
		h(Toast, {
			...toast,
			modelValue: toast.show,
			'onUpdate:modelValue': (val) => (toast.show = val),
		})
	)
  },
}

export function createToast(options) {
	let toast = reactive({
		key: 'toast-' + toasts.value.length,
		show: false,
		...options,
	})
	setTimeout(() => {
		toast.show = true
	}, 0)
	toasts.value.push(toast)
}