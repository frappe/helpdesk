<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import {
  AGENT_PORTAL_LANDING,
  CUSTOMER_PORTAL_LANDING,
  KB_PUBLIC,
} from "@/router";

const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();

function getTarget() {
  if (authStore.hasDeskAccess) return AGENT_PORTAL_LANDING;
  else if (configStore.preferKnowledgeBase) return KB_PUBLIC;
  else return CUSTOMER_PORTAL_LANDING;
}

router.push({ name: getTarget() });
</script>
