<template>
    <div class="flow-root border-b pt-2 pb-3 pr-8">
        <div class="float-left ml-4">
            <div class="flex items-center space-x-4">
                <Button appearance="secondary">Close</Button>
                <Button appearance="secondary">Delete</Button>
            </div>
        </div>
        <div class="float-right">
            <div class="flex items-cnter space-x-4">
                <Button icon="chevron-left" />
                <span class="text-base py-1">1 of 15</span>
                <Button icon="chevron-right" />
            </div>
        </div>
    </div>
</template>

<script>
export default {
	name: "TicketTopPanel"
}
</script>

<style>

</style>