<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { useRouter } from "vue-router";

const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();

function getTarget() {
  if (authStore.hasDeskAccess) return "TicketsAgent";
  else if (configStore.preferKnowledgeBase) return "CustomerKnowledgeBase";
  else return "TicketsCustomer";
}

router.push({ name: getTarget() });
</script>
