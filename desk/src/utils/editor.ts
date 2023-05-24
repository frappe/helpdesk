import { isEmpty as isEmpty_ } from "lodash";

export function strip(content: string) {
	const opening = new RegExp(/^<div class='content-block'><div>/);
	const closing = new RegExp(/<\/div><\/div>$/);

	return content.replace(opening, "").replace(closing, "");
}

/**
 * Check if the content is empty. This is done by replacing all <div class="content-block">
 * with empty strings.
 */
export function isEmpty(content: string) {
	return isEmpty_(strip(content).trim());
}
