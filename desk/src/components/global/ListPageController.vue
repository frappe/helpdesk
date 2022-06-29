<template>
    <div v-if="!manager.loading && !(manager.list.length == 0 && manager.start == 0)" class="flex justify-center">
        <div v-if="manager.hasPage(2)" class="flex flex-row space-x-2">
            <Button v-if="manager.hasPage(manager.currPage -1)" appearance="minimal" icon-left="chevron-left" @click="manager.previousPage()">Previous</Button>
            <Button appearance="primary"> {{ manager.currPage }} </Button>
            <Button v-if="manager.hasPage(manager.currPage + 1)" appearance="minimal" @click="manager.getPage(manager.currPage + 1)"> {{ manager.currPage + 1 }} </Button>
            <Button v-if="manager.hasPage(manager.currPage + 2)" appearance="minimal" @click="manager.getPage(manager.currPage + 2)"> {{ manager.currPage + 2 }}</Button>
            <Button v-if="manager.hasPage(manager.currPage + 1)" appearance="minimal" icon-right="chevron-right" @click="manager.nextPage()">Next</Button>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ListPageController',
    props: ['manager']
}
</script>

<style>

</style>