# Bulk Reply

Send the same reply to multiple tickets in one go — useful for outage updates, mass announcements, or batch follow-ups.

## Who can use it

Anyone with the **Agent** role. Each ticket is checked individually for write permission, so a reply is only sent to tickets you can edit.

## How to use it

1. Open the **Tickets** list view.
2. Select the tickets you want to reply to using the checkboxes in the list.
3. In the selection banner at the bottom, click **Bulk Reply**.
4. Compose your reply in the modal:
   - Your email **signature** is added automatically (if you've set one in *Settings → Profile → Email Settings*).
   - Click the paperclip icon to add **attachments**. The same files will be attached to every ticket's reply.
   - Use the formatting toolbar for bold, italics, lists, links, etc.
5. Click **Send to N tickets** (or **Send Reply** if you selected one).

**Shortcut:** press `Cmd/Ctrl + Enter` while the editor is focused to send.

## What happens behind the scenes

For each selected ticket the system:

- Creates a new **Communication** record linked to the ticket.
- Links every attachment to both the new Communication and the ticket (so they appear in the ticket's attachments tab).
- Sends the reply email to the ticket's original requester (`raised_by`), using your default outgoing email account.
- Records the send in the ticket's activity log.

The original ticket subject is reused with a `Re:` prefix, and the reply is threaded as a response to the most recent communication on that ticket (so customers see it in the same email thread).

## Things to know

- **Recipient** — the reply goes to the email address that originally raised each ticket. There is currently no way to override the recipient per ticket from the bulk modal.
- **One message, many tickets** — the message body is identical for every ticket. Use it for content that genuinely applies to all of them.
- **Attachments are shared** — every selected ticket gets the same set of attachments attached to its reply.
- **Signature** — pulled from your user profile. If you don't have one set, no signature is added.
- **Drafts** — the modal does not save drafts. Closing it clears the editor.

## Limitations

- The send is **synchronous** — for very large selections the request may take a while; keep the tab open until you see the confirmation toast.
- Individual ticket failures (for example, a bad email account on one ticket) are logged but do **not** stop the rest of the batch. The success toast reflects how many tickets were dispatched, not how many emails reached the inbox. Check **Error Log** for details if you suspect a partial failure.
- Duplicate ticket IDs in the selection are ignored.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Send button is disabled | A file is still uploading, or the editor is empty. Wait for the upload to finish or type a message. |
| Signature didn't appear | Set one in *Settings → Profile → Email Settings* and reopen the modal. |
| Reply didn't reach the customer | Check the ticket's *Communications* tab to confirm the message was created, then check **Error Log** for SMTP/email-account errors. |
| "Not permitted" error | You don't have write permission on at least one of the selected tickets. Deselect tickets outside your team and try again. |
