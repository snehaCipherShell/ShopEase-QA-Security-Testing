# Explaining ShopEase in an Interview

## 30-second version
"ShopEase is a fictional e-commerce app I built and tested locally to practise QA and basic security testing. I wrote a test plan, designed manual test cases with boundary analysis, automated API tests with pytest, built a Postman collection, validated data with SQL and ran local security checks like access control and price tampering."

## Structure (about 2 minutes)
**Objective:** show end-to-end tester skills on a small system; cover both QA and entry-level security validation.
**Approach:** requirements -> scenarios -> detailed cases (EP/BVA) -> manual + API + SQL + security checks -> bug reports. Each automated test uses a fresh temporary database so tests are independent and repeatable.
**Tools:** Python/Flask/SQLite (the app), pytest and requests, Postman, sqlite3, browser DevTools, Git.
**Challenges:** (1) deciding what a *correct* response is for another user's order (I chose 404 to avoid revealing which IDs exist, and documented it); (2) making logout truly invalidate sessions - I used server-side session tokens so an old cookie fails after logout; (3) test isolation; (4) finding that the dev server added its own `Server` banner, so my first fix did not work and I needed a custom request handler.
**Results (say only what you ran):** "My latest pytest run on my machine passed all 185 tests (Python 3.14, pytest 8.4). I also replayed the manual and security cases at API level with a script: 42 of 42 passed. Two real low-severity defects were found and fixed with regression tests: the server banner leaking versions (BUG-001) and HTTP 500 on oversized IDs (BUG-002). The browser-based manual cases and the Postman collection are still marked Not Run, and one cosmetic bug (BUG-003) is open."
**Honest limits:** local app, no certified audit, no UI automation, no rate limiting or CSRF tests yet.
**Future improvements:** Selenium/Playwright UI tests, CI with GitHub Actions, rate-limit and CSRF tests, dependency scanning, TLS locally.

## Tips
- Never claim the app is "secure"; say what you tested and how.
- Be ready to explain every line of a test you wrote; open one in the interview (e.g. `test_user_cannot_read_another_users_order`).
- Mention that severity/priority depend on context, and that DevTools evidence suggests but does not prove a root cause.

## Practice questions based on this project
**QA**
1. How did you choose the cart quantity test values? (EP/BVA: 0, 1, 10, 11 plus wrong types)
2. What is the difference between severity and priority? Give an example from your bug log.
3. Why did you verify results with SQL as well as the API?
4. How do you make automated tests independent and repeatable? (fresh temp DB and server per test)
5. What did your tests find, and what could they not find?

**Junior penetration testing**
1. How did you test for broken object-level authorization (IDOR) on orders, and why does the API return 404?
2. Why must the server calculate prices, and how did you test price tampering?
3. How do you verify that logout really ends a session?
4. Which cookie flags matter, and why is `Secure` off in your local setup?
5. What is the difference between a confirmed vulnerability and a potential risk in your findings document?
