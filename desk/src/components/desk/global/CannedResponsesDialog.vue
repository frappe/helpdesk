<template>
    <div>
        <Dialog :options="{ title: 'Canned responses'}"
                :show="show"
                @close="close()"
        >
        <template #body-content>
            <div class="space-y-6 flex flex-row">
                <Input 
                    v-model="search"
                    id="searchInput"
                    class="w-full"
                    type="text"
                    placeholder="Search for response"
                    @input="getCannedResponses"
                />
            </div>
            <div class="divide-y divide-slate-200 ">
            <div v-for="item in this.cannedResponses" class="relative py-1">
                <CustomIcons
                    name="add-new"
                    class="h-7 w-7 rounded p-1 mb-4 absolute right-0"
                    role="button"
                    
                    @click="addMessage(item);emitMessage();close()"

                />
            <Accordion class="my-2">
            <template v-slot:title>
                <span class="font-medium text-lg ">{{item.title}}</span>
            </template>
            <template v-slot:content>
                <div v-html="item.message" class="font-normal text-lg text-grey ml-5">
                    
                </div>
                    
            </template>

        </Accordion>
    </div>
</div>
        </template>
            
        </Dialog>
    </div>
</template>

<script>
import { Dialog,FeatherIcon, Input } from "frappe-ui"
import Accordion from "@/components/global/Accordion.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import {ref,computed,provide} from "vue"
export default{
    name:"CannedResponsesDialog",
    props:["show"],
    components:{
        Dialog,
        FeatherIcon,
        Accordion,
        CustomIcons
    },
    setup (){
        const listManager=ref([])
        const tempMessage=ref("")
        provide("tempMessage",tempMessage)
        return {
            listManager,
            tempMessage
        }
    },
    data(){
        return {
            cannedResponses:[]
        }
    },
    methods:{
        close(){
            this.$emit("close")
            this.$emit('messageVal',this.$refs.tempMessage)
        },
        emitMessage(){
            this.$emit('messageVal',this.$refs.tempMessage)
        },
        addMessage(item){
            this.$refs.tempMessage=item.message
        },
        getCannedResponses(event){
    
            let title = event
            this.$resources.list.fetch({
                    title:title
                })
        }         
    },
    resources:{
        list(){
            
           return {
            method:"frappedesk.api.cannedResponse.get_canned_response",
            onSuccess(val){
                this.cannedResponses=val
                return this.cannedResponses
            }   
            }
        }
    },
    beforeMount(){
        this.getCannedResponses()
    }
}
</script>