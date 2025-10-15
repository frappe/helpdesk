import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

export function useActiveTabManager(tabs) {
  const route = useRoute();
  const router = useRouter();

  const changeTabTo = (tab) => {
    tabIndex.value = tab;
    setActiveTabInUrl(tabs.value?.[tab]?.name || tabs.value[0].name);
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

  watch(
    () => route.hash,
    (newHash) => {
      let index = findTabIndex(newHash.replace("#", ""));
      if (index === -1) index = 0;

      tabIndex.value = index;
    }
  );

  watch(
    tabs,
    (tabsValue) => {
      if (!tabsValue?.length) return;

      let _activeTab = route.hash.replace("#", "");
      if (_activeTab) {
        let index = findTabIndex(_activeTab);
        if (index !== -1) {
          tabIndex.value = index;
          setActiveTabInUrl(tabsValue[index].name);
          return;
        }
      }
      tabIndex.value = 0;
      setActiveTabInUrl(tabsValue[0].name);
    },
    { deep: true, flush: "post" }
  );

  return { tabIndex, changeTabTo };
}
