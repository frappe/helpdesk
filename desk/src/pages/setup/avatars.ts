import { createAvatar } from "@dicebear/core";
import * as lorelei from "@dicebear/lorelei";

const cache = new Map<string, string>();

/** A stable DiceBear lorelei face for a seed, as an SVG data URI. */
export function avatarFor(seed: string): string {
  let uri = cache.get(seed);
  if (!uri) {
    uri = createAvatar(lorelei, { seed }).toDataUri();
    cache.set(seed, uri);
  }
  return uri;
}
