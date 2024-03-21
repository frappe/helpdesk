<template>
  <div class="min-w-[490px] px-[24px] py-[10px]">
    <div class="flow-root h-[72px] shrink-0 py-[22px] px-[16px]">
      <div class="float-left">
        <RouterLink
          to="/canned-responses"
          class="my-1 flex select-none flex-row items-center space-x-1 stroke-gray-600 text-sm text-gray-600 hover:stroke-gray-700 hover:text-gray-700"
          role="button"
        >
          <FeatherIcon name="arrow-left" class="h-[13px] w-[13px]" />
          <div>Back to response list</div>
        </RouterLink>
      </div>
      <div class="float-right">
        <div v-if="!editMode" class="flex flex-row space-x-2">
          <Button
            appearance="secondary"
            @click="
              () => {
                editMode = true;
                newAResponseTempValues = {
                  title: cannedResponseDoc.title,
                  message: cannedResponseDoc.message,
                };
              }
            "
            >Edit</Button
          >
        </div>
        <div v-else class="flex flex-row space-x-2">
          <Button
            appearance="secondary"
            @click="
              () => {
                $router.go();
              }
            "
          >
            Cancel
          </Button>
          <Button appearance="primary" @click="saveResponse()"> Save </Button>
        </div>
      </div>
    </div>
    <div
      class="flex h-full flex-row space-x-[24px] border-t px-[16px] py-[22px]"
    >
      <ResponseTitleAndMessage
        class="grow"
        :title="values?.cannedResponseName"
        :message="values?.message"
        :editable="editMode"
        :response-resource="$resources.cannedResponse"
      />
    </div>
  </div>
</template>
<script>
import { ref, provide } from "vue";
import { FeatherIcon, Input } from "frappe-ui";
import ResponseTitleAndMessage from "@/components/desk/settings/canned_responses/ResponseTitleAndMessage.vue";

export default {
  name: "CannedResponseInfo",
  components: {
    FeatherIcon,
    Input,
    ResponseTitleAndMessage,
  },
  props: ["canned_response"],
  setup(props) {
    const editingName = ref(false);
    const newResponseTempValues = ref({});
    const updateNewResponseInput = ref((input) => {
      newResponseTempValues.value[input.field] = input.value;
    });
    provide("updateNewResponseInput", updateNewResponseInput);
    provide("newResponseTempValues", newResponseTempValues);
    const saveResponseTitleAndMessage = ref(() => {});
    provide("saveResponseTitleAndMessage", saveResponseTitleAndMessage);
    const tempCannedResponseName = ref("");
    const updatingValues = ref(false);
    const editMode = ref(!props.canned_response);
    provide("editMode", editMode);

    return {
      editingName,
      tempCannedResponseName,
      updatingValues,
      editMode,
      newResponseTempValues,
      saveResponseTitleAndMessage,
    };
  },
  computed: {
    cannedResponseDoc() {
      return this.$resources.cannedResponse.doc || null;
    },
    values() {
      if (this.updatingValues) {
        return this.values || null;
      }
      return {
        cannedResponseName: this.cannedResponseDoc?.title || null,
        message: this.cannedResponseDoc?.message || null,
      };
    },
  },
  deactivated() {
    this.resetForm();
  },
  resources: {
    cannedResponse() {
      return {
        type: "document",
        doctype: "HD Canned Response",
        name: this.canned_response,
        setValue: {
          onSuccess: () => {
            this.$toast({
              title: "Canned Response Updated.",
              icon: "check",
              iconClasses: "text-green-500",
            });
          },
          onError: (err) => {
            this.$toast({
              title: "Error while updating canned response",
              text: err,
              icon: "x",
              iconClasses: "text-red-500",
            });
          },
        },
      };
    },
  },
  methods: {
    resetForm() {
      this.editingName = false;
      this.tempCannedResponseName = this.values.cannedResponseName;
    },
    save() {
      this.updatingValues = true;
      const newValues = this.values;
      this.$resources.user.setValue
        .submit({
          title: newValues.title,
          message: newValues.message,
        })
        .then(() => {
          this.$resources.cannedResponse.setValue.submit({
            title: this.tempCannedResponseName,
          });
        });
    },
    saveResponse() {
      const inputParams = {
        title: this.newResponseTempValues.title,
        message: this.newResponseTempValues.message,
      };
      this.$resources.cannedResponse.setValue.submit({
        ...inputParams,
      });
      this.editMode = false;
    },
    cancel() {
      this.$router.go();
    },
  },
};
</script>
