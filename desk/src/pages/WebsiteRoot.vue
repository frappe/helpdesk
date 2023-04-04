<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const router = useRouter();

const AGENT_PORTAL_LANDING = "DeskTickets";
const CUSTOMER_PORTAL_LANDING = "PortalTickets";

if (authStore.hasDeskAccess) router.replace({ name: AGENT_PORTAL_LANDING });
else router.replace({ name: CUSTOMER_PORTAL_LANDING });
</script>
