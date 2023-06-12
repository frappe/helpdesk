<template>
  <div class="h-full overflow-auto p-5">
    <div
      v-if="
        !isNew &&
        ($resources.getSlaPolicy.loading ||
          $resources.updateServicePolicy.loading)
      "
    >
      <LoadingText text="Fetching policy..." />
    </div>
    <div v-else>
      <div class="mb-4 flow-root">
        <div class="float-left">
          <div v-if="!$resources.renameServicePolicy.loading">
            <div
              v-if="!editingName"
              class="flex items-center space-x-2"
              :class="slaPolicyName != 'Default' ? 'cursor-pointer' : ''"
              @click="editPolicyName()"
            >
              <div class="font-semibold">{{ slaPolicyName }}</div>
              <FeatherIcon
                v-if="slaPolicyName != 'Default'"
                class="h-3 w-3"
                name="edit"
              />
            </div>
            <div v-else class="flex items-center space-x-2">
              <Input
                v-model="tempSlaPolicyName"
                type="text"
                placeholder="Enter Policy Name"
              />
              <FeatherIcon
                class="h-4 w-4 cursor-pointer"
                name="x"
                @click="
                  () => {
                    editingName = false;
                    tempSlaPolicyName = slaPolicyName;
                  }
                "
              />
            </div>
          </div>
          <div v-else>
            <LoadingText text="Renaming..." />
          </div>
        </div>
        <div class="float-right">
          <div class="flex items-center space-x-2">
            <Button appearance="secondary" @click="cancel()">Cancel</Button>
            <Button
              v-if="isNew"
              :loading="$resources.createNewServicePolicy.loading"
              appearance="primary"
              @click="create()"
              >Create</Button
            >
            <Button
              v-else
              :loading="$resources.updateServicePolicy.loading"
              appearance="primary"
              @click="save()"
              >Save</Button
            >
          </div>
        </div>
      </div>
      <div class="mb-5">
        <div class="flex items-center space-x-2">
          <div class="text-base font-semibold">Rules</div>
        </div>
        <div>
          <div class="text-base">
            <div class="flex border-b py-4 text-gray-600">
              <div class="w-2/12">Priority</div>
              <div class="w-1/12">Default</div>
              <div class="w-3/12 text-right">First Response Time</div>
              <div class="w-3/12 text-right">Resolution Time</div>
            </div>
            <div v-for="(rule, index) in rules" :key="rule.priority">
              <div
                class="flex items-center py-2 text-gray-900"
                :class="index < rules.length - 1 ? 'border-b' : ''"
              >
                <div class="w-2/12">
                  <Dropdown
                    v-if="ticketPriorityStore.options"
                    :options="prioritiesAsDropdownOptions(index)"
                    class="w-full cursor-pointer text-base"
                  >
                    <template
                      #default="{ togglePriority }"
                      class="w-full"
                      @click="togglePriority"
                    >
                      <div class="flex items-center space-x-2">
                        <div class="text-left">
                          {{ rule.priority }}
                        </div>
                        <!-- <FeatherIcon name="chevron-down" class="h-4 w-4" /> -->
                      </div>
                    </template>
                  </Dropdown>
                </div>
                <div class="w-1/12">
                  <CustomSwitch
                    v-model="rule.default"
                    @click="changeDefaultPriority(index)"
                  />
                </div>
                <div class="flex w-3/12 flex-row-reverse">
                  <TimeDurationInput v-model="rule.firstResponseTime" />
                </div>
                <div class="flex w-3/12 flex-row-reverse">
                  <TimeDurationInput v-model="rule.resolutionTime" />
                </div>
              </div>
            </div>
          </div>
        </div>
        <ErrorMessage :message="rulesValidationError" />
      </div>
      <div>
        <div class="mb-3 flex items-center space-x-2">
          <div class="text-base font-semibold">Working Hours</div>
        </div>
        <div>
          <p class="text-base text-gray-700">
            Choose the days in a week, and start and end times to set as working
            hours.
          </p>
          <div class="space-y-3 py-4 text-gray-900">
            <div v-for="workingHour in workingHours" :key="workingHour.workday">
              <div class="flex h-7 items-center text-base">
                <div class="w-2/12">
                  {{ workingHour.workday }}
                </div>
                <div class="flex w-2/12 items-center space-x-2">
                  <CustomSwitch v-model="workingHour.enabled" />
                  <span class="sr-only">{{
                    `${workingHour.enabled ? "Open" : "Closed"}`
                  }}</span>
                  <div>
                    {{ workingHour.enabled ? "Open" : "Closed" }}
                  </div>
                </div>
                <div
                  v-if="workingHour.enabled"
                  class="flex w-6/12 items-center space-x-4"
                >
                  <input
                    v-model="workingHour.from"
                    class="w-28 rounded border-0 bg-gray-100 p-1 text-base"
                    type="time"
                  />
                  <div class="text-gray-600">TO</div>
                  <input
                    v-model="workingHour.to"
                    class="w-28 rounded border-0 bg-gray-100 p-1 text-base"
                    type="time"
                  />
                </div>
              </div>
            </div>
            <ErrorMessage :message="workingHoursValidationError" />
          </div>
          <div class="space-y-4">
            <Dropdown
              v-if="serviceHolidayList"
              :options="serviceHolidayListDropdownOptions()"
              class="w-53 cursor-pointer text-base"
              placement="left"
            >
              <template
                #default="{ toggleHolidayList }"
                class="w-full"
                @click="toggleHolidayList"
              >
                <div class="flex items-center space-x-2">
                  <div>
                    <span class="mb-2 block text-sm leading-4 text-gray-700"
                      >Holidays on</span
                    >
                    <div
                      class="form-input block w-52 px-3 placeholder:text-gray-500"
                    >
                      {{ selectedHolidayList }}
                    </div>
                  </div>
                </div>
              </template>
            </Dropdown>
            <ErrorMessage :message="holidayListValidationError" />
          </div>
        </div>
        <div class="mt-5 flow-root">
          <div class="float-left">
            <Button appearance="secondary" @click="cancel()">Cancel</Button>
          </div>
          <div class="float-right">
            <Button
              v-if="isNew"
              :loading="$resources.createNewServicePolicy.loading"
              appearance="primary"
              @click="create()"
              >Create</Button
            >
            <Button
              v-else
              :loading="$resources.updateServicePolicy.loading"
              appearance="primary"
              @click="save()"
              >Save</Button
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
import {
  FeatherIcon,
  Input,
  LoadingText,
  Dropdown,
  ErrorMessage,
} from "frappe-ui";
import TimeDurationInput from "@/components/desk/global/TimeDurationInput.vue";
import CustomSwitch from "@/components/global/CustomSwitch.vue";
import { useTicketPriorityStore } from "@/stores/ticketPriority";

export default {
  name: "SlaPolicy",
  components: {
    FeatherIcon,
    Input,
    LoadingText,
    Dropdown,
    ErrorMessage,
    TimeDurationInput,
    CustomSwitch,
  },
  props: ["id"],
  setup() {
    const isNew = ref(false);

    const slaPolicyName = ref("");
    const editingName = ref(false);
    const tempSlaPolicyName = ref("");
    const selectedHolidayList = ref("");

    const rulesValidationError = ref("");
    const workingHoursValidationError = ref("");
    const holidayListValidationError = ref("");

    const rules = ref([]);
    const workingHours = ref([]);

    const ticketPriorityStore = useTicketPriorityStore();

    return {
      isNew,
      slaPolicyName,
      tempSlaPolicyName,
      editingName,
      rules,
      workingHours,
      ticketPriorityStore,
      selectedHolidayList,
      rulesValidationError,
      workingHoursValidationError,
      holidayListValidationError,
    };
  },
  computed: {
    priorities() {
      return this.rules.map((rule) => {
        return {
          priority: rule.priority,
          default_priority: rule.default,
          response_time: rule.firstResponseTime,
          resolution_time: rule.resolutionTime,
        };
      });
    },
    supportAndResolution() {
      return this.workingHours
        .map((workingHour) => {
          if (workingHour.enabled) {
            return {
              workday: workingHour.workday,
              start_time: workingHour.from,
              end_time: workingHour.to,
            };
          }
        })
        .filter((x) => x);
    },
    serviceHolidayList() {
      return this.$resources.getServiceHolidayList.data || null;
    },
  },
  mounted() {
    this.$event.emit("set-selected-setting", "Support Policies");
    this.$event.emit("show-top-panel-actions-settings", "Support Policy");

    this.isNew = this.$route.name === "NewSlaPolicy";
    this.editingName = false;
    if (this.isNew) {
      this.setDefaultValues();
    } else {
      this.$resources.getSlaPolicy.fetch();
    }
  },
  resources: {
    getSlaPolicy() {
      return {
        url: "frappe.client.get",
        params: {
          doctype: "HD Service Level Agreement",
          name: this.id,
          fields: ["*"],
        },
        onSuccess: (data) => {
          this.slaPolicyName = data.name;
          this.selectedHolidayList = data.holiday_list;
          this.rules = data.priorities.map((priority) => {
            return {
              priority: priority.priority,
              default: priority.default_priority,
              firstResponseTime: priority.response_time,
              resolutionTime: priority.resolution_time,
            };
          });
          let sanitizerTimeStr = (timeStr) => {
            let timeList = timeStr.split(":");
            let newTimeStr = "";
            timeList.forEach((t, index) => {
              newTimeStr += t.length == 2 ? t : "0".concat(t);
              if (index < timeList.length - 1) {
                newTimeStr += ":";
              }
            });
            return newTimeStr;
          };
          this.workingHours = data.support_and_resolution.map((workingHour) => {
            return {
              workday: workingHour.workday,
              enabled: true,
              from: sanitizerTimeStr(workingHour.start_time),
              to: sanitizerTimeStr(workingHour.end_time),
            };
          });

          let weekdays = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
          ];
          weekdays.forEach((day) => {
            if (!this.workingHours.find((x) => x.workday == day)) {
              this.workingHours.push({
                workday: day,
                enabled: false,
                from: "00:00:00",
                to: "00:00:00",
              });
            }
          });

          this.workingHours = this.workingHours.sort((a, b) => {
            return (
              weekdays.findIndex((x) => x == a.workday) -
              weekdays.findIndex((x) => x == b.workday)
            );
          });
        },
      };
    },
    updateServicePolicy() {
      return {
        url: "frappe.client.set_value",
      };
    },
    createNewServicePolicy() {
      return {
        url: "frappe.client.insert",
        onSuccess: () => {
          this.$router.push({
            name: "SlaPolicies",
          });
        },
      };
    },
    renameServicePolicy() {
      return {
        url: "frappe.client.rename_doc",
      };
    },
    getServiceHolidayList() {
      return {
        url: "helpdesk.extends.client.get_list",
        params: {
          doctype: "HD Service Holiday List",
          fields: ["*"],
        },
        auto: true,
        onSuccess: (data) => {
          if (data.length > 0) {
            this.selectedHolidayList = data[0].holiday_list_name;
          }
        },
      };
    },
  },
  methods: {
    setDefaultValues() {
      this.slaPolicyName = "New Service Policy";
      this.tempSlaPolicyName = this.slaPolicyName;

      this.rules = [
        {
          priority: "Urgent",
          default: false,
          firstResponseTime: 30 * 60,
          resolutionTime: 2 * 3600,
        },
        {
          priority: "High",
          default: false,
          firstResponseTime: 1 * 3600,
          resolutionTime: 4 * 3600,
        },
        {
          priority: "Medium",
          default: true,
          firstResponseTime: 8 * 3600,
          resolutionTime: 24 * 3600,
        },
        {
          priority: "Low",
          default: false,
          firstResponseTime: 24 * 3600,
          resolutionTime: 72 * 3600,
        },
      ];
      this.workingHours = [
        {
          workday: "Monday",
          enabled: true,
          from: "09:00",
          to: "17:00",
        },
        {
          workday: "Tuesday",
          enabled: true,
          from: "09:00",
          to: "17:00",
        },
        {
          workday: "Wednesday",
          enabled: true,
          from: "09:00",
          to: "17:00",
        },
        {
          workday: "Thursday",
          enabled: true,
          from: "09:00",
          to: "17:00",
        },
        {
          workday: "Friday",
          enabled: true,
          from: "09:00",
          to: "17:00",
        },
        {
          workday: "Saturday",
          enabled: false,
          from: "09:00",
          to: "17:00",
        },
        {
          workday: "Sunday",
          enabled: false,
          from: "09:00",
          to: "17:00",
        },
      ];
    },
    editPolicyName() {
      if (this.slaPolicyName != "Default") {
        this.tempSlaPolicyName = this.slaPolicyName;
        this.editingName = true;
      }
    },
    changeDefaultPriority(index) {
      this.rules.forEach((rule, i) => {
        if (i == index) {
          rule.default = true;
        } else {
          rule.default = false;
        }
      });
    },
    rename() {
      // TODO: once Service level agreement is renamable uncomment this block
      // return this.$resources.renameServicePolicy.submit({
      // 	doctype: "HD Service Level Agreement",
      // 	old_name: this.slaPolicyName,
      // 	new_name: this.tempSlaPolicyName
      // })
    },
    create() {
      // TODO: validate inputs
      if (this.validateInputs()) {
        this.$resources.createNewServicePolicy.submit({
          doc: {
            doctype: "HD Service Level Agreement",
            service_level: this.tempSlaPolicyName,
            priorities: this.priorities,
            support_and_resolution: this.supportAndResolution,
            document_type: "HD Ticket",
            holiday_list: this.selectedHolidayList,
            sla_fulfilled_on: [{ status: "Resolved" }, { status: "Closed" }],
            pause_sla_on: [{ status: "Replied" }],
            enabled: true,
          },
        });
      }
    },
    save() {
      if (this.validateInputs()) {
        this.$resources.updateServicePolicy
          .submit({
            doctype: "HD Service Level Agreement",
            name: this.slaPolicyName,
            fieldname: {
              priorities: this.priorities,
              support_and_resolution: this.supportAndResolution,
            },
          })
          .then(() => {
            if (this.slaPolicyName != this.tempSlaPolicyName) {
              this.rename();
            }
            this.$toast({
              title: "Policy updated",
              icon: "check",
              iconClasses: "text-green-500",
            });
          });
      }
    },
    validateInputs() {
      this.rulesValidationError = "";
      this.workingHoursValidationError = "";
      this.holidayListValidationError = "";

      let errors = [];

      if (!this.selectedHolidayList) {
        this.holidayListValidationError = "A holiday list should be selected";
        errors.push(this.holidayListValidationError);
      }

      let startTimeAfterEndTime = false;
      this.supportAndResolution.forEach((workingHour) => {
        if (workingHour.start_time > workingHour.end_time) {
          startTimeAfterEndTime = true;
        }
      });

      if (startTimeAfterEndTime) {
        this.workingHoursValidationError =
          "Start time should not be after end time";
        errors.push(this.workingHoursValidationError);
      }

      let defaultPrioritySelected = false;
      let timeDurationIsZero = false;
      this.priorities.forEach((priority) => {
        if (priority.default_priority) {
          defaultPrioritySelected = true;
        }
        if (priority.resolution_time == 0 || priority.response_time == 0) {
          timeDurationIsZero = true;
        }
      });
      if (!defaultPrioritySelected) {
        this.rulesValidationError = "Default rule needs to be selected";
        errors.push(this.rulesValidationError);
      }
      if (timeDurationIsZero) {
        this.rulesValidationError =
          "Response and resolution time should not be 0";
        errors.push(this.rulesValidationError);
      }
      return errors.length == 0;
    },
    cancel() {
      this.$router.go();
    },
    prioritiesAsDropdownOptions(index) {
      let priorityItems = [];
      if (this.ticketPriorityStore.options) {
        this.ticketPriorityStore.options.forEach((priority) => {
          priorityItems.push({
            label: priority.name,
            onClick: () => {
              this.rules[index].priority = priority.name;
            },
          });
        });
        return priorityItems;
      } else {
        return null;
      }
    },
    serviceHolidayListDropdownOptions() {
      let serviceHolidayListItems = [];
      if (this.serviceHolidayList) {
        this.serviceHolidayList.forEach((holiday) => {
          serviceHolidayListItems.push({
            label: holiday.name,
            onClick: () => {
              // TODO: selecte the service holiday list
              this.selectedHolidayList = holiday.name;
            },
          });
        });
        return serviceHolidayListItems;
      } else {
        return null;
      }
    },
  },
};
</script>

<style></style>
