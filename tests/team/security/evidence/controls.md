| id | control | check | expected | observed | result |
|---|---|---|---|---|---|
| CT-01 | session cookie | sid is HttpOnly, SameSite=Lax, Secure | HttpOnly true, SameSite Lax, Secure true when served over HTTPS | HttpOnly true, SameSite Lax, Secure false (site served over plain HTTP), expires in 170 h | pass (Secure not testable without HTTPS) |
| CT-02 | CSRF token | POST /api new ticket without, then with, X-Frappe-CSRF-Token | without token: rejected, nothing created; with token: created | without: HTTP 400 CSRFTokenError: Invalid Request; tickets 13 -> 13; with: HTTP 200 | pass |
| CT-03 | session end | replay the sid cookie after logout | old session id no longer grants access | before logout HTTP 200; replayed sid after logout HTTP 401 | pass |
| CT-04 | sign-in errors | wrong password for an existing account vs an unknown account | same status and same message | existing: HTTP 401 "Invalid login credentials"; unknown: HTTP 401 "Invalid login credentials" | pass |
| CT-05 | server-side role check | customer sends a priority change the screen does not offer | no control on screen, and the direct request refused | priority control shown: 0; direct PUT HTTP 403 PermissionError: You do not have permission to change Priority; stored priority Medium | pass |
