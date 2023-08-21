import { io } from "socket.io-client";
import { socketio_port } from "../../../../sites/common_site_config.json";

function initSocket() {
  const host = window.location.hostname;
  const port = window.location.port ? `:${socketio_port}` : "";
  const protocol = port ? "http" : "https";
  const siteName = window["site_name"];
  const namespace = !siteName?.startsWith("{{") ? siteName : host;
  const url = `${protocol}://${host}${port}/${namespace}`;
  const socket = io(url, { withCredentials: true });
  return socket;
}

export const socket = initSocket();
