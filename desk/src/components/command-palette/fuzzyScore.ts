import type { Command } from "./paletteTypes";

/**
 * Score for one row: the best of its title, keywords and subtitle, scaled by
 * weight. Keywords and subtitle are penalised so a title match always wins a
 * tie. Kept beside the scorer, and free of Vue imports, so the ranking that
 * decides which row Enter runs can be checked in isolation.
 */
export function scoreCommand(command: Command, term: string): number {
  if (command.rank !== undefined) return command.rank;
  if (!term) return 0;
  const base = Math.max(
    fuzzyScore(command.title, term),
    command.keywords ? fuzzyScore(command.keywords, term) - 50 : -1,
    command.subtitle ? fuzzyScore(command.subtitle, term) - 100 : -1
  );
  if (base < 0) return -1;
  return base * (command.weight ?? 1);
}

/**
 * Subsequence scorer for the command palette. Prefix beats substring beats
 * scattered match; -1 means no match at all. Small enough to not warrant a
 * dependency, and kept dependency-free so it can be checked in isolation.
 */
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
