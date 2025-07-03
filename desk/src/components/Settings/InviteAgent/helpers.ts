export function getEmailsErrorMsg(emails: readonly string[], type: "present" | "invited") {
    return `User${
        emails.length > 1 ? "s" : ""
      } with email ${emails.join(", ")} already ${type}`
}

export function getId() {
  return String(Math.random());
}
