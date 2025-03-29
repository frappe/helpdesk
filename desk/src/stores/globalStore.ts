import { getCurrentInstance } from "vue";

export const globalStore = () => {
  const app = getCurrentInstance();
  const { $dialog, $socket } = app.appContext.config.globalProperties;

  return {
    $dialog,
    $socket,
  };
};
