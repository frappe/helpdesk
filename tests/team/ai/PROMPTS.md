# Prompts

Every prompt typed to the AI agent in this project, verbatim and in order,
taken from the Claude Code session transcript by `tools/extract_prompts.py`.
Times are UTC. "choice" rows are answers picked from options the agent
offered; "setting" rows are changes made in the app, not prompts.
Short prompts such as "Mutation testing" were the label of a button the
agent offered as the next step.

The full transcript, which also holds the agent's replies and every command
it ran, is kept by the team outside the repository (it contains local paths
and account details) and can be shown on request.

## 1. 2026-11-16 13:06 (prompt)

```text
@"C:\Users\Administrator\Downloads\SQE_Final_Project Fall 2026.pdf"
for this sqe task i need you to choose a git hub repo and do its testing for me and choose frappe on github and use it for this project
```

## 2. 2026-11-16 13:07 (choice)

```text
"Frappe" on GitHub is an organisation with several apps. Your brief needs a web-based MIS with two related workflows, and ERPNext itself is banned. Which Frappe repository should the project use?

Chosen: frappe/helpdesk (Recommended)
```

## 3. 2026-11-16 13:10 (prompt)

```text
what do you recommend
```

## 4. 2026-11-16 13:29 (prompt)

```text
done
```

## 5. 2026-11-16 13:34 (prompt)

```text
Yes, user created
```

## 6. 2026-11-16 14:00 (prompt)

```text
continue when the install is done
```

## 7. 2026-11-16 14:10 (prompt)

```text
Approve, start tests
```

## 8. 2026-11-16 16:22 (prompt)

```text
Mutation testing
```

## 9. 2026-11-17 04:53 (prompt)

```text
API tests + generator
```

## 10. 2026-11-17 05:21 (prompt)

```text
Playwright use cases
```

## 11. 2026-11-17 05:59 (prompt)

```text
Three members
```

## 12. 2026-11-17 06:39 (prompt)

```text
Usability + accessibility
```

## 13. 2026-11-17 16:51 (prompt)

```text
<command-name>/model</command-name>
            <command-message>model</command-message>
            <command-args>claude-opus-5-5</command-args>
```

## 14. 2026-11-17 16:51 (setting)

```text
Set model to `claude-opus-5-5`
```

## 15. 2026-11-17 16:51 (prompt)

```text
continue with accessibility
```

## 16. 2026-11-17 17:12 (prompt)

```text
continue when the scans finish
```

## 17. 2026-11-17 17:14 (prompt)

```text
Security checks
```

## 18. 2026-11-17 17:55 (prompt)

```text
Performance
```

## 19. 2026-11-17 19:39 (prompt)

```text
SonarQube
```

## 20. 2026-11-17 22:01 (prompt)

```text
Test management docs
```

## 21. 2026-11-18 06:35 (prompt)

```text
I'll paste the URL
```

## 22. 2026-11-18 09:44 (prompt)

```text
give me step by step instructions on how to do it
```

## 23. 2026-11-18 10:05 (prompt)

```text
remote: Repository not found.
fatal: repository 'https://github.com/OWNER/helpdesk.git/' not found
```

## 24. 2026-11-18 10:07 (prompt)

```text
https://github.com/ibbster05/helpdesk
```

## 25. 2026-11-18 12:09 (prompt)

```text
AI-use record
```

## 26. 2026-11-18 12:41 (prompt)

```text
Fix DEF-02/03
```

## 27. 2026-11-18 17:00 (choice)

```text
For DEF-03, who may a ticket be assigned to? Upstream's test_non_agent_flow assigns a ticket to a portal (Website) user with no roles and expects that to work, so the stricter rule will make that one upstream test fail.

Chosen: Agents only (Recommended)
```

## 28. 2026-11-18 17:56 (prompt)

```text
Fix DEF-14
```
