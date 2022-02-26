<template>
  <div class="w-full">
	<Combobox v-model="selected">
	  <div class="relative mt-1">
		<div
		  class="relative w-full text-left bg-white rounded-lg shadow-md cursor-default focus:outline-none focus-visible:ring-2 focus-visible:ring-opacity-75 focus-visible:ring-white focus-visible:ring-offset-teal-300 focus-visible:ring-offset-2 sm:text-sm overflow-hidden"
		>
		  <ComboboxInput
			class="w-full border-none focus:ring-0 py-2 pl-3 pr-10 text-sm leading-5 text-gray-900"
			:displayValue="(person) => person.name"
			@change="query = $event.target.value"
		  />
		  <ComboboxButton
			class="absolute inset-y-0 right-0 flex items-center pr-2"
		  >
		  </ComboboxButton>
		</div>
		<TransitionRoot
		  leave="transition ease-in duration-100"
		  leaveFrom="opacity-100"
		  leaveTo="opacity-0"
		>
		  <ComboboxOptions
			class="absolute w-full py-1 mt-1 overflow-auto text-base bg-white rounded-md shadow-lg max-h-60 ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
		  >
			<div
			  v-if="filteredPeople.length === 0 && query !== ''"
			  class="cursor-default select-none relative py-2 px-4 text-gray-700"
			>
			  Nothing found.
			</div>

			<ComboboxOption
			  v-for="person in filteredPeople"
			  as="template"
			  :key="person.id"
			  :value="person"
			  v-slot="{ selected, active }"
			>
			  <li
				class="cursor-default select-none relative py-2 pl-10 pr-4"
				:class="{
				  'text-white bg-teal-600': active,
				  'text-gray-900 bg-white': !active,
				}"
			  >
				<span
				  class="block truncate"
				  :class="{ 'font-medium': selected, 'font-normal': !selected }"
				>
				  {{ person.name }}
				</span>
				<span
				  v-if="selected"
				  class="absolute inset-y-0 left-0 flex items-center pl-3"
				  :class="{ 'text-white': active, 'text-teal-600': !active }"
				>
				</span>
			  </li>
			</ComboboxOption>
		  </ComboboxOptions>
		</TransitionRoot>
	  </div>
	</Combobox>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import {
  Combobox,
  ComboboxInput,
  ComboboxButton,
  ComboboxOptions,
  ComboboxOption,
  TransitionRoot,
} from '@headlessui/vue'

const people = [
  { id: 1, name: 'Wade Cooper' },
  { id: 2, name: 'Arlene Mccoy' },
  { id: 3, name: 'Devon Webb' },
  { id: 4, name: 'Tom Cook' },
  { id: 5, name: 'Tanya Fox' },
  { id: 6, name: 'Hellen Schmidt' },
]

export default {
  components: {
	Combobox,
	ComboboxInput,
	ComboboxButton,
	ComboboxOptions,
	ComboboxOption,
	TransitionRoot,
  },
  setup() {
	let selected = ref(people[0])
	let query = ref('')

	let filteredPeople = computed(() =>
	  query.value === ''
		? people
		: people.filter((person) =>
			person.name
			  .toLowerCase()
			  .replace(/\s+/g, '')
			  .includes(query.value.toLowerCase().replace(/\s+/g, ''))
		  )
	)

	return { selected, query, filteredPeople }
  },
}
</script>
