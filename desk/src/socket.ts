import { io } from "socket.io-client";
import { getCachedResource, getCachedListResource } from "frappe-ui";
import { socketio_port } from "../../../../sites/common_site_config.json";

function init() {
  const url = getUrl();
  const socket = io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
  });

  socket.on("refetch_resource", (data) => {
    if (data.cache_key) {
      const resource =
        getCachedResource(data.cache_key) ||
        getCachedListResource(data.cache_key);
      if (resource) {
        resource.reload();
      }
    }
  });

  return socket;
}

function getUrl() {
  const host = window.location.hostname;
  const port = window.location.port ? `:${socketio_port}` : "";
  const protocol = port ? "http" : "https";
  const fVersion = window["frappe_version"];
  if (fVersion && fVersion.startsWith("14")) {
    return `${protocol}://${host}${port}`;
  }
  const siteName = window["site_name"];
  const namespace = !siteName?.startsWith("{{") ? siteName : host;
  return `${protocol}://${host}${port}/${namespace}`;
}

export const socket = init();
