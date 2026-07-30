import type { Command } from "./paletteTypes";

/** Every substring hit scores at least this; scattered subsequences never do. */
const SUBSTRING_SCORE = 800;

/** Best of title, keywords (−50) and subtitle (−100), scaled by weight — the
 * penalties keep a visible-title match winning any tie. */
export function scoreCommand(command: Command, term: string): number {
  if (command.rank !== undefined) return command.rank;
  if (!term) return 0;
  const base = Math.max(
    fuzzyScore(command.title, term),
    command.keywords ? fuzzyScore(command.keywords, term) - 50 : -1,
    command.subtitle ? fuzzyScore(command.subtitle, term) - 100 : -1
  );
  if (base < 0) return -1;
  // A scattered hit like "sett" would un-hide every "Set status: …" row at once.
  if (command.hideWhenEmpty && base < SUBSTRING_SCORE) return -1;
  return base * (command.weight ?? 1);
}

/** Prefix beats substring beats scattered subsequence; -1 means no match. */
export function fuzzyScore(text: string, term: string): number {
  if (!term) return 0;
  const haystack = (text ?? "").toLowerCase();
  const needle = term.toLowerCase();

  const direct = haystack.indexOf(needle);
  if (direct === 0) return 1000;
  if (direct > 0) {
    const onWordBoundary = /[\s\-_#/]/.test(haystack[direct - 1] ?? "");
    return 900 - Math.min(direct, 100) + (onWordBoundary ? 60 : 0);
  }

  let position = 0;
  let streak = 0;
  let longestStreak = 0;
  let gaps = 0;
  for (const char of needle) {
    const found = haystack.indexOf(char, position);
    if (found === -1) return -1;
    if (found === position && position > 0) {
      streak += 1;
    } else {
      gaps += found - position;
      streak = 0;
    }
    longestStreak = Math.max(longestStreak, streak);
    position = found + 1;
  }
  return 400 + longestStreak * 20 - Math.min(gaps, 200);
}
