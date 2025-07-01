// Simple translation plugin similar to Drive
function translate(message, replace) {
	let translatedMessages = window.frappe?.boot?.__messages || {};
	let translatedMessage = translatedMessages[message] || message;

	if (replace && typeof replace === "object") {
		// Simple placeholder replacement
		for (let key in replace) {
			translatedMessage = translatedMessage.replace(new RegExp(`{${key}}`, 'g'), replace[key]);
		}
	}

	return translatedMessage;
}

export const translationsPlugin = {
	install(app) {
		app.config.globalProperties.__ = translate;
		app.provide("$translate", translate);
		window.__ = translate;
	},
}
