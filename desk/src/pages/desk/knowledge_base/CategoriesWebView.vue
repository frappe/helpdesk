<template>
    <div class="rounded shadow p-5 h-full overflow-y-scroll">
        <KBHome :editable="true"/>
    </div>
</template>

<script>
import KBHome from '@/components/global/KBHome.vue';
import { provide } from '@vue/runtime-core';

export default {
    name: 'CategoriesWebView',
    props: {
        categoryId: {
            type: String,
            default: null
        },
        parentCategoryId: {
            type: String,
            default: null
        }
    },
    components: {
        KBHome
    },
    setup(props) {
        provide('categoryId', props.categoryId)
        if (props.parentCategoryId) {
            provide('parentCategoryId', props.parentCategoryId)
        }
    }
}
</script>