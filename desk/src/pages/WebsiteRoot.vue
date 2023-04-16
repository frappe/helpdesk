<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { AGENT_PORTAL_LANDING, CUSTOMER_PORTAL_LANDING } from "@/router";

const authStore = useAuthStore();
const router = useRouter();

if (authStore.hasDeskAccess) router.replace({ name: AGENT_PORTAL_LANDING });
else router.replace({ name: CUSTOMER_PORTAL_LANDING });
</script>
