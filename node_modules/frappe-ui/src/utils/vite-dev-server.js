module.exports = {
  getProxyOptions({ port }) {
    return {
      '^/(app|api|assets|files)': {
        target: `http://localhost:${port}`,
        ws: true,
        router: function (req) {
          const site_name = req.headers.host.split(':')[0]
          return `http://${site_name}:${port}`
        },
      },
    }
  },
}
