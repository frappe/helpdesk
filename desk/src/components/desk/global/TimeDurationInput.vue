<template>
	<div
		v-on-outside-click="
			() => {
				editing = false
			}
		"
	>
		<div>
			<div
				class="cursor-pointer w-24 text-right p-1.5 bg-gray-100 rounded"
				@click="
					() => {
						editing = !editing
					}
				"
			>
				{{ convertSecondsToTimeStr(modelValue) }}
			</div>
		</div>
		<div v-if="editing" class="relative">
			<div class="absolute z-10 rounded shadow bg-white p-3 mt-2">
				<div class="flex space-x-2">
					<div class="space-y-1">
						<Input class="w-16" v-model="hours" type="number" />
						<div>hours</div>
					</div>
					<div class="space-y-1">
						<Input class="w-16" v-model="minutes" type="number" />
						<div>minutes</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input } from "frappe-ui"
import { ref } from "@vue/reactivity"

export default {
	name: "TimeDurationInput",
	props: ["modelValue"],
	components: {
		Input,
	},
	setup() {
		const hours = ref(0)
		const minutes = ref(0)
		const timeStr = ref("")

		const editing = ref(false)

		return {
			hours,
			minutes,
			timeStr,
			editing,
		}
	},
	mounted() {
		if (this.modelValue) {
			this.timeStr = this.convertSecondsToTimeStr(this.modelValue)

			let time = this.convertSecondsToHoursAndMinutes(this.modelValue)
			this.hours = time.hours ? time.hours : 0
			this.minutes = time.minutes ? time.minutes : 0
		}
	},
	watch: {
		hours(newValue) {
			this.updateModelValue()
		},
		minutes(newValue) {
			this.updateModelValue()
		},
	},
	methods: {
		updateModelValue() {
			this.$emit(
				"update:modelValue",
				this.convertTimeStToSeconds(
					`${this.hours ? this.hours : "0"}h ${
						this.minutes ? this.minutes : "0"
					}m`
				)
			)
		},
		convertSecondsToTimeStr(seconds) {
			let time = this.convertSecondsToHoursAndMinutes(seconds)

			let h = time.hours
			let m = time.minutes

			let hStr = h > 0 ? `${h}h` : ""
			let mStr = m > 0 ? `${m}m` : ""

			return `${hStr} ${mStr}`.trim() || "0h 0m"
		},
		convertTimeStToSeconds(strTime) {
			let timeList = strTime.split(" ")
			let seconds = 0
			timeList.forEach((t) => {
				if (t.includes("h")) {
					seconds += t.replace("h", "") * 3600
				} else if (t.includes("m")) {
					seconds += t.replace("m", "") * 60
				}
			})
			return seconds
		},
		convertSecondsToHoursAndMinutes(seconds) {
			let hours = Math.floor(seconds / 3600)
			let minutes = Math.floor((seconds % 3600) / 60)

			return {
				hours,
				minutes,
			}
		},
	},
}
</script>

<style></style>
