<template>
    <div>
    <div 
        v-if="!editable"
        class="flex flex-col space-y-[16px] rounded-[8px] border shadow-sm p-[32px]"
    >
    <div
        class="font-semibold text-[24px] prose prose-p:my-1 border-b pb-[16px] mb-[10px]"
    >
        {{title}}

    </div>
    <div
        class="overflow-y-scroll"
        style="
            min-height: calc(100vh - 500px);
            max-height: calc(100vh - 245px);
        "
        v-html="message"
    >
    </div>
        
    </div>
    <div v-else>
        <div class="flex flex-col space-y-[16px] h-full">
            <div>
                <input
                    class="border-gray-400 placeholder-gray-500 form-input block w-full"
                    label="Title"
                    type="text"
                    :value="title"
                    @input="(val)=>{
                        tempNewTitle=val
                    }"
                />
            </div>
            <div>
                <CustomTextEditor 
                :show="true"
                ref="contentEditor"
                @click="$refs.contentEditor.focusEditor()"
                :content="message"
                @change="(val)=>{
                    tempNewMessage=val
                }"
                editorClasses="w-full p-[12px] bg-gray-100 min-h-[180px] max-h-[500px] text-[16px]"
                class="rounded-[8px]"            
                >
                <template #top-section="{ editor }">
                    <div class="flex flex-col">
                        <div class="block mb-2 text-sm leading-4 text-gray-700">
                            Message
                        </div>
                        <div class="flex flex-row items-center space-x-1.5 p-1.5 rounded-t-[8px] border bg-gray-50">
                            <div 
                                v-for="item in [
                                    'bold',
									'italic',
									'|',
									'quote',
									'code',
									'|',
									'numbered-list',
									'bullet-list',
									'left-align',
									'center-align',
									'right-align',
                                ]"
                                :key="item"
                            >
                            <TextEditorMenuItem
                                :item="item"
                                :editor="editor"
                            />
                            </div>
                        </div>
                    </div>
                </template>
                </CustomTextEditor>
            </div>
        </div>
    </div>
    </div>
</template>

<script>
import CustomTextEditor from "@/components/global/CustomTextEditor.vue"
import TextEditorMenuItem from "@/components/global/TextEditorMenuItem.vue"
import { ref, inject } from "vue"
export default {
	name: "ResponseTitleAndMessage",
	props: ["title", "message", "editable", "responseResource"],
	components: {
		CustomTextEditor,
		TextEditorMenuItem,
	},
	mounted() {
		this.saveResponseTitleAndMessage = this.save
	},
	watch: {
		tempNewTitle(val) {
			this.updateNewResponseInput({ field: "title", value: val })
		},
		tempNewMessage(val) {
			this.updateNewResponseInput({ field: "message", value: val })
		},
	},
	setup(props) {
		const tempNewTitle = ref(props.title)
		const tempNewMessage = ref(props.message)
		const editMode = inject("editMode")
		const updateNewResponseInput = inject("updateNewResponseInput")
		const saveResponseTitleAndMessage = inject("saveResponseTitleAndMessage")
		return {
			tempNewTitle,
			tempNewMessage,
			editMode,
			updateNewResponseInput,
			saveResponseTitleAndMessage,
		}
	},
	methods: {
		save() {
			this.responseResource.setValue.submit({
				title: this.tempNewTitle,
				message: this.tempNewMessage,
			})
			this.editMode = false
		},
        
	},
}
</script>