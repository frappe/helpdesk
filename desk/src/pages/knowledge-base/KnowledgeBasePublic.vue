<template>
  <div
    class="flex bg-gray-100"
    :style="{
      height: '220px',
    }"
  >
    <div class="container m-auto space-y-2">
      <div
        class="text-3xl font-semibold text-gray-900"
        :style="{
          'font-size': '40px',
        }"
      >
        Knowldege Base
      </div>
      <div class="w-max border-b border-gray-600 pb-1 text-lg text-gray-700">
        Track tickets
      </div>
    </div>
  </div>
  <div class="container m-auto">
    <RouterView />
  </div>
</template>
