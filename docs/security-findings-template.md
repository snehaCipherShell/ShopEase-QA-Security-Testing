# Security Findings Template and Register

**Rules:** one finding per entry; only include what you actually observed; attach evidence; never invent CVEs, scan output, CVSS scores or successful exploitation. Separate **Confirmed** findings (reproducible evidence) from **Potential risks** (hypotheses or design observations that are not proven). Test only authorised, local targets.

## Finding template
| Field | Content |
|---|---|
| Finding ID | SEC-F-NNN |
| Title | |
| Classification | Confirmed vulnerability / Potential risk / Informational |
| Affected component | endpoint, page, file |
| Related test case | SEC-... |
| Environment / build | commit hash, config, date |
| Description | what is wrong, in plain words |
| Preconditions | |
| Steps to reproduce | numbered, with exact requests |
| Expected behaviour | |
| Actual behaviour | |
| Evidence | request/response, screenshot, log, SQL output |
| Impact | what could happen *in this app's context* |
| Severity and rationale | Low / Medium / High / Critical + reasoning (likelihood x impact, access needed, data affected) |
| Recommendation | |
| Status | Open / Fixed / Retested / Accepted risk |

## Findings register (real, from the author's work on this repository)
| ID | Title | Classification | Severity | Status |
|---|---|---|---|---|
| SEC-F-001 | `Server` header disclosed Werkzeug and Python versions | Confirmed (observed in a test failure; same as BUG-001) | Low | Fixed; regression test PASSED in the user's pytest run (E07) and `Server: ShopEase` seen in E12 |
| SEC-F-002 | Unhandled `OverflowError` -> HTTP 500 for integer IDs >= 2^63 (BUG-002) | Confirmed (reviewer execution, 2026-10-10) | Low | **Fixed and verified**: 5 regression tests + full pytest run 185 passed (2026-10-12) |

No other confirmed vulnerabilities are recorded. That statement is limited to what was executed or evidenced (see `docs/security-test-report.md`); it is **not** a claim that ShopEase is secure.

## Known limitations / potential risks (design review, NOT confirmed vulnerabilities and NOT tested)
| ID | Observation | Why it matters | Idea to explore |
|---|---|---|---|
| PR-01 | No rate limiting or account lockout on `/api/auth/login` (confirmed by reading the code that it is not implemented) | Repeated password guessing is not slowed | Add throttling, then test it (locally only) |
| PR-02 | No CSRF tokens. Mitigations present: `SameSite=Lax` cookie, JSON-only `Content-Type` check | Whether this is sufficient depends on browser behaviour; not tested | Build a local HTML page on a different local origin to examine behaviour (authorised, local only) |
| PR-03 | Plain HTTP on localhost; cookie has no `Secure` flag by documented design | Fine locally, unacceptable on a real network | Run behind local TLS and set `SHOPEASE_COOKIE_SECURE=1` |
| PR-04 | Registration reveals when a username/email already exists | Account enumeration | Decide trade-off; consider generic response |
| PR-05 | Flask development server is not a production server | Not hardened | Use a production WSGI server and reverse proxy in real deployments |
| PR-06 | No audit logging of security events | Harder incident investigation | Add structured logs |
| PR-07 | Sessions are not bound to IP/User-Agent | Stolen cookies work from anywhere until expiry | Evaluate trade-offs |

## Blank entry
| Field | Content |
|---|---|
| Finding ID | SEC-F-003 |
| Title | |
| Classification | |
| Evidence | |
