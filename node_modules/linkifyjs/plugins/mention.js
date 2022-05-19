typeof console !== 'undefined' && console && console.warn && console.warn('"linkifyjs/plugins/mention" is deprecated in v3. Please install "linkify-plugin-mention" instead');
require('../lib/plugins/mention');
module.exports = () => {}; // noop for compatibility with v2
