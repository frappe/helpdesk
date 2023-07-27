<template>
  <div class="min-w-[490px] px-[24px] py-[10px]">
    <div class="flow-root h-[72px] shrink-0 py-[22px] px-[16px]">
      <div class="float-left">
        <RouterLink
          :to="`/ticket-types`"
          class="my-1 flex select-none flex-row items-center space-x-1 stroke-gray-600 text-sm text-gray-600 hover:stroke-gray-700 hover:text-gray-700"
          role="button"
        >
          <FeatherIcon name="arrow-left" class="h-[13px] w-[13px]" />
          <div>Back to ticket type list</div>
        </RouterLink>
      </div>
      <div class="float-right">
        <div class="flex flex-row space-x-2">
          <Button appearance="secondary" @click="cancel()"> Cancel </Button>
          <Button
            appearance="primary"
            @click="
              () => {
                if (validate()) {
                  save();
                }
              }
            "
          >
            Save
          </Button>
        </div>
      </div>
    </div>

    <div
      v-if="ticketType"
      class="flex h-full flex-row space-x-[24px] border-t px-[16px] py-[22px]"
    >
      <div class="flex h-full w-full flex-col space-y-[16px]">
        <div>
          <Input
            label="Title"
            type="text"
            :value="ticketType.name"
            @input="
              (val) => {
                newTicketTypeValues.title = val;
              }
            "
          />
          <ErrorMessage :message="ticketTypeInputErrors.title" />
        </div>
        <div class="w-full space-y-1">
          <div>
            <span class="block text-sm leading-4 text-gray-700">
              Priority
            </span>
          </div>
          <Autocomplete
            :value="newTicketTypeValues.priority"
            :resource-options="{
              url: 'helpdesk.extends.client.get_list',
              inputMap: (query) => {
                return {
                  doctype: 'HD Ticket Priority',
                  pluck: 'name',
                  filters: [['name', 'like', `%${query}%`]],
                };
              },
              responseMap: (res) => {
                return res.map((d) => {
                  return {
                    label: d.name,
                    value: d.name,
                  };
                });
              },
            }"
            @change="
              (item) => {
                if (!item) {
                  return;
                }
                newTicketTypeValues.priority = item.value;
              }
            "
          />
        </div>
        <div class="flex flex-col">
          <div class="mb-2 block text-sm leading-4 text-gray-700">
            Description
          </div>
          <TextEditor
            ref="textEditor"
            :class="'bg-gray-100'"
            :editor-class="'min-h-[20rem] overflow-y-auto max-h-[73vh] px-3 max-w-full'"
            :content="ticketType.description"
            :starterkit-options="{
              heading: { levels: [2, 3, 4, 5, 6] },
            }"
            @change="
              (val) => {
                newTicketTypeValues.description = val;
              }
            "
          >
          </TextEditor>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { ref } from "vue";
import { FeatherIcon, Input, ErrorMessage, TextEditor } from "frappe-ui";
import Autocomplete from "@/components/global/Autocomplete.vue";
export default {
  name: "TicketTypeInfo",
  components: {
    FeatherIcon,
    Input,
    Autocomplete,
    TextEditor,
    ErrorMessage,
  },
  props: ["ticketTypeId"],
  setup() {
    const newTicketTypeValues = ref({
      title: "",
      priority: "",
      description: "",
    });
    const ticketTypeInputErrors = ref({
      title: "",
    });
    return {
      newTicketTypeValues,
      ticketTypeInputErrors,
    };
  },
  computed: {
    ticketType() {
      if (this.ticketTypeId) {
        const doc = this.$resources.ticketType.doc;
        if (doc) {
          this.newTicketTypeValues.title = doc.name;
          this.newTicketTypeValues.priority = doc.priority;
          this.newTicketTypeValues.description = doc.description;
        }
        return doc;
      } else {
        return { title: "", description: "", priority: "" };
      }
    },
  },
  resources: {
    ticketType() {
      if (!this.ticketTypeId) return;
      return {
        type: "document",
        doctype: "HD Ticket Type",
        name: this.ticketTypeId,
        setValue: {
          onSuccess: () => {
            this.$toast({
              title: "Ticket Type Updated.",
              icon: "check",
              iconClasses: "text-green-500",
            });
          },
          onError: (err) => {
            this.$toast({
              title: "Error while updating ticket type",
              text: err,
              icon: "x",
              iconClasses: "text-red-500",
            });
          },
        },
      };
    },
    renameTicketTypeDoc() {
      return {
        url: "frappe.client.rename_doc",
        onSuccess: (res) => {
          this.$router.push({
            path: `/ticket-types/${res}`,
          });
        },
      };
    },
    newTicketType() {
      return {
        url: "frappe.client.insert",
        onSuccess: (res) => {
          this.$router.push({
            path: `/ticket-types/${res.name}`,
          });
        },
      };
    },
  },
  methods: {
    validate() {
      if (this.newTicketTypeValues.title === "") {
        this.ticketTypeInputErrors.title = "Ticket Type name is required";
        return false;
      } else if (this.newTicketTypeValues.title == "new") {
        this.ticketTypeInputErrors.title = "Ticket Type name cannot be 'new'";
        return false;
      }
      return true;
    },
    save() {
      const oldTicketTypeName = this.ticketType.name;
      const newTicketTypeName = this.newTicketTypeValues.title;
      const values = this.newTicketTypeValues;
      if (this.ticketTypeId) {
        this.$resources.ticketType.setValue
          .submit({
            priority: values.priority,
            description: values.description,
          })
          .then(() => {
            if (newTicketTypeName != oldTicketTypeName) {
              this.$resources.renameTicketTypeDoc.submit({
                doctype: "HD Ticket Type",
                old_name: oldTicketTypeName,
                new_name: newTicketTypeName,
              });
            }
          });
      } else {
        this.$resources.newTicketType.submit({
          doc: {
            doctype: "HD Ticket Type",
            name: values.title,
            description: values.description,
            priority: values.priority,
          },
        });
      }
    },
    cancel() {
      this.$router.go();
    },
  },
};
</script>
