<template>
  <div
    v-if="isMobileView"
    class="flex items-center justify-between gap-2 px-5 pb-4 pt-3"
  >
    <Filter
      :filters="filter.filters"
      :filterable-fields="filter.filterableFields"
      @event:filter="(e) => emitToParent(e, 'event:filter')"
    />
    <div class="flex items-center gap-2">
      <Button :label="'Refresh'" @click="emit('event:reload')">
        <template #icon>
          <RefreshIcon class="h-4 w-4" />
        </template>
      </Button>

      <Sort
        :sortable-fields="sort.sortableFields"
        :sorts="sort.sorts"
        @event:sort="(e) => emitToParent(e, 'event:sort')"
        :hide-label="isMobileView"
      />
      <ColumnSettings
        :fields="column.fields"
        :columns="column.columns"
        @event:column="(e) => emitToParent(e, 'event:column')"
        :hide-label="isMobileView"
      />
    </div>
  </div>
  <div v-else class="flex items-center justify-between gap-2 px-5 pb-4 pt-3">
    <div class="flex items-center gap-2">
      <Dropdown :options="presetFilters">
        <template #default="{ open }">
          <Button :label="currentPreset">
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
              />
            </template>
          </Button>
        </template>
      </Dropdown>
    </div>
    <div class="-mr-2 h-[70%] border-l" />
    <FadedScrollableDiv
      class="flex flex-1 items-center overflow-x-auto px-1"
      orientation="horizontal"
    >
      <div
        v-for="quickFilter in quickFilterList"
        :key="quickFilter.name"
        class="min-w-36 m-1"
      >
        <FormControl
          type="text"
          :placeholder="quickFilter.label"
          :debounce="500"
          @change.stop="updateFilter(quickFilter, $event.target.value)"
        />
      </div>
    </FadedScrollableDiv>
    <div class="grow"></div>

    <div class="flex items-center gap-2">
      <Button :label="'Refresh'" @click="emit('event:reload')">
        <template #icon>
          <RefreshIcon class="h-4 w-4" />
        </template>
      </Button>
      <Filter
        :filters="filter.filters"
        :filterable-fields="filter.filterableFields"
        @event:filter="(e) => emitToParent(e, 'event:filter')"
      />
      <Sort
        :sortable-fields="sort.sortableFields"
        :sorts="sort.sorts"
        @event:sort="(e) => emitToParent(e, 'event:sort')"
      />
      <ColumnSettings
        :fields="column.fields"
        :columns="column.columns"
        :is-customer-portal="isCustomerPortal"
        @event:column="(e) => emitToParent(e, 'event:column')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h } from "vue";
import { Dropdown, FeatherIcon, FormControl } from "frappe-ui";
import { Filter, Sort, ColumnSettings, FadedScrollableDiv } from "@/components";
import { useAuthStore } from "@/stores/auth";
import { RefreshIcon } from "@/components/icons";
import { useScreenSize } from "@/composables/screen";

const authStore = useAuthStore();
let currentPreset = ref("All Tickets");

const props = defineProps({
  filter: {
    type: Object,
    required: true,
  },
  sort: {
    type: Object,
    required: true,
  },
  column: {
    type: Object,
    required: true,
  },
  isCustomerPortal: {
    type: Boolean,
    default: false,
  },
});

const { isMobileView } = useScreenSize();

const quickFilterList = computed(() => {
  let filters = [{ name: "name", label: "ID", fieldtype: "Data" }];
  return filters;
});

const presetFilters = computed(() => {
  const _presetFilters = [
    {
      label: "All Tickets",
      onClick: (e) => {
        setTitle("Helpdesk");
        emitToParent(
          {
            event: "clear",
          },
          "event:filter"
        );
      },
    },
    {
      label: "My Open Tickets",
      onClick: (e) => {
        const preset = getPresetFilters("Open");
        emitToParent(
          {
            event: "preset",
            data: preset,
          },
          "event:filter"
        );
      },
    },
    {
      label: "My Closed Tickets",
      onClick: (e) => {
        const preset = getPresetFilters("Closed");
        emitToParent(
          {
            event: "preset",
            data: preset,
          },
          "event:filter"
        );
      },
    },
  ];
  if (!props.isCustomerPortal) {
    _presetFilters.push(
      {
        label: "My Replied Tickets",
        onClick: (e) => {
          const preset = getPresetFilters("Replied");
          emitToParent(
            {
              event: "preset",
              data: preset,
            },
            "event:filter"
          );
        },
      },
      {
        label: "My Resolved Tickets",
        onClick: (e) => {
          const preset = getPresetFilters("Resolved");
          emitToParent(
            {
              event: "preset",
              data: preset,
            },
            "event:filter"
          );
        },
      }
    );
  }
  return _presetFilters;
});

function setTitle(title: string) {
  document.title = title;
}

function getPresetFilters(status: string) {
  setTitle(`My ${status} Tickets`);
  document.title = `My ${status} Tickets`;

  const filtersToApply = {
    status: ["=", status],
  };

  const filters = [
    {
      field: props.filter.filterableFields.find(
        (f) => f.fieldname === "status"
      ),
      operator: "is",
      value: status,
    },
  ];

  if (!props.isCustomerPortal) {
    filtersToApply["_assign"] = ["LIKE", `%${authStore.userId}%`];
    filters.push({
      field: props.filter.filterableFields.find(
        (f) => f.fieldname === "_assign"
      ),
      operator: "is",
      value: authStore.userId,
    });
  }

  return {
    filters,
    filtersToApply,
  };
}

const emit = defineEmits([
  "event:filter",
  "event:sort",
  "event:column",
  "event:reload",
]);

function emitToParent(data, event) {
  if (event === "event:filter") {
    if (data.event === "clear") {
      currentPreset.value = "All Tickets";
    } else {
      currentPreset.value = "Filtered Tickets";
    }
  }
  emit(event, data);
}

function updateFilter(filter, value) {
  if (value === "") {
    emitToParent(
      {
        event: "remove",
        name: filter.name,
      },
      "event:filter"
    );
    return;
  } else {
    emitToParent(
      {
        event: "add",
        data: {
          field: {
            fieldname: filter.name,
            fieldtype: filter.fieldtype,
            label: filter.label,
          },
          filterToApply: {
            [filter.name]: ["=", value],
          },
          operator: "equals",
          value: value,
        },
      },
      "event:filter"
    );
  }
}
</script>
