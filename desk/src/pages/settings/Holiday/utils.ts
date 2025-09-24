export const getRepetitionText = (repetition: any) => {
  const parts: string[] = [];

  if (repetition.all) {
    parts.push("week");
  } else {
    if (repetition.first) parts.push("first");
    if (repetition.second) parts.push("second");
    if (repetition.third) parts.push("third");
    if (repetition.fourth) parts.push("fourth");
    if (repetition.fifth) parts.push("fifth");

    if (parts.length === 0) return "";

    if (parts.length > 1) {
      const last = parts.pop();
      parts[parts.length - 1] = `${parts[parts.length - 1]} and ${last}`;
    }

    parts[0] = parts[0].charAt(0) + parts[0].slice(1);
    return `Every ${parts.join(", ")} week`;
  }

  return parts[0] ? `Every ${parts[0]}` : "";
};
