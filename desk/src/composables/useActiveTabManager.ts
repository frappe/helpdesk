import { useTelephonyStore } from "@/stores/telephony";
import { storeToRefs } from "pinia";
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

export function useActiveTabManager(tabs) {
  const route = useRoute();
  const router = useRouter();
  const telephonyStore = useTelephonyStore();
  const { isLoading: isTelephonyLoading } = storeToRefs(telephonyStore);

  const changeTabTo = (tab) => {
    tabIndex.value = tab;
    if (tab == 0) {
      router.replace({ path: route.path });
    } else {
      setActiveTabInUrl(tabs.value?.[tab]?.name || tabs.value[0].name);
    }
  };

  function setActiveTabInUrl(tabName) {
    let hash = "#" + tabName?.toLowerCase();
    if (route.hash === hash) return;
    router.push({ hash, query: route.query });
  }

  function findTabIndex(tabName) {
    return tabs.value?.findIndex(
      (tabOptions) => tabOptions.name.toLowerCase() === tabName
    );
  }

  const tabIndex = ref(0);

  const setActiveTab = () => {
    let _activeTab = route.hash.replace("#", "");
    if (_activeTab) {
      let index = findTabIndex(_activeTab);
      if (index !== -1 || index === 0) {
        tabIndex.value = index;
        setActiveTabInUrl(tabs.value[index].name);
        return;
      }
    }

    tabIndex.value = 0;
    router.replace({ path: route.path });
  };

  // Handle when page is navigated
  watch(
    () => route.hash,
    (newHash) => {
      let index = findTabIndex(newHash.replace("#", ""));
      if (index === -1) index = 0;

      if (index == 0) {
        router.replace({ path: route.path });
      }

      tabIndex.value = index;
    }
  );

  // Handle when tabs array is updated
  watch(
    [tabs, isTelephonyLoading],
    ([tabsValue, isLoading]) => {
      if (!tabsValue?.length) return;
      if (!isLoading) {
        setActiveTab();
      }
    },
    { deep: true, flush: "post" }
  );

  return { tabIndex, changeTabTo };
}
