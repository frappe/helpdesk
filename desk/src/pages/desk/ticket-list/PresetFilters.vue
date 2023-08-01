<template>
  <Dropdown :options="options">
    <template #default="{ open }">
      <div class="flex cursor-pointer items-center gap-2">
        <div class="text-2xl font-semibold text-gray-900">
          {{ title }}
        </div>
        <Icon
          :icon="open ? 'lucide:chevron-up' : 'lucide:chevron-down'"
          class="h-5 w-5"
        />
      </div>
    </template>
  </Dropdown>
</template>

<script>
import { ref } from "vue";
import { Dropdown } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { useConfigStore } from "@/stores/config";
import { useFilter } from "@/composables/filter";

export default {
  name: "PresetFilters",
  components: {
    Dropdown,
    Icon,
  },
  setup() {
    const configStore = useConfigStore();
    const { storage, setQuery } = useFilter();
    const presetFilters = ref([]);
    const presetTitle = ref("");

    return {
      configStore,
      setQuery,
      storage,
      presetFilters,
      presetTitle,
    };
  },
  computed: {
    currentQuery() {
      return this.$route.query.q;
    },
    title() {
      if (this.presetTitle) return this.presetTitle;
      if (this.currentQuery) return "Filtered Tickets";
      return "All Tickets";
    },
    presets() {
      return this.$resources.presetFilterOptions.data || [];
    },
    options() {
      let options = [];
      let data = this.presets;
      if (Object.keys(data).length) {
        Object.keys(data).forEach((group) => {
          if (data[group].length) {
            options.push({
              group: group === "user" ? "My Filters" : "Global",
              hideLabel: group !== "user",
              items: data[group].map((item) => {
                return {
                  label: item.title,
                  onClick: () => {
                    this.storage.clear();
                    item.filters.forEach((f) =>
                      this.storage.add({
                        fieldname: f.fieldname,
                        operator: f.filter_type,
                        value: f.value,
                      })
                    );
                    this.setQuery();
                  },
                };
              }),
            });
          }
        });
      }

      return options;
    },
  },
  watch: {
    title(newTitle) {
      this.configStore.setTitle(newTitle);
    },
  },
  mounted() {
    this.configStore.setTitle(this.title);
    this.$socket.on("helpdesk:new-preset-filter", (data) => {
      if (data.reference_doctype !== "HD Ticket") return;
      this.$resources.presetFilterOptions.reload();
    });
  },
  unmounted() {
    this.configStore.setTitle();
    this.$socket.off("helpdesk:new-preset-filter");
  },
  resources: {
    presetFilterOptions() {
      return {
        url: "helpdesk.api.general.get_preset_filters",
        params: {
          doctype: "HD Ticket",
        },
        cache: ["Preset Filter", this.doctype],
        auto: true,
      };
    },
  },
};
</script>
