import { isEmpty as isEmpty_ } from "lodash";

export function strip(content: string) {
	const opening = new RegExp(/^<p>/);
	const closing = new RegExp(/<\/p>$/);

	return content.replace(opening, "").replace(closing, "");
}

/**
 * Check if the content is empty with empty strings
 */
export function isEmpty(content: string) {
	return isEmpty_(strip(content).trim());
}
