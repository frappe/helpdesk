<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { CUSTOMER_PORTAL_ROOT } from "@/utils";
import { useRouter } from "vue-router";

const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();

if (authStore.hasDeskAccess) {
  router.push({ name: "TicketsAgent" });
} else if (configStore.preferKnowledgeBase) {
  router.push({ name: "CustomerKnowledgeBase" });
} else {
  window.location.replace(CUSTOMER_PORTAL_ROOT);
}
</script>
