# QA Concepts with ShopEase Examples

## 1. QA vs QC vs Testing
| Term | Focus | ShopEase example |
|---|---|---|
| **QA** (Quality Assurance) | *Process* - preventing defects | Agreeing validation rules (password 8-64 chars) before coding; code review; having this test plan |
| **QC** (Quality Control) | *Product* - detecting defects in the built product | Running TC-REG-003 and checking the system rejects a 7-char password |
| **Software testing** | The activity of executing/evaluating software to find defects and gather information; a main QC activity | Running `pytest`, Postman, manual cases |

## 2. Verification vs Validation
- **Verification** - "Are we building the product *right*?" (reviews, static checks, comparing to the spec). Example: reviewing that requirement R-06 says shipping is free at >= 50.00 and the code uses `>= 5000` cents.
- **Validation** - "Are we building the *right* product?" (running it, checking it meets user needs). Example: checking out with a cart and seeing that the total a customer would expect is charged.

## 3. SDLC and STLC
SDLC phases: requirements -> design -> development -> testing -> deployment -> maintenance. STLC phases: requirement analysis -> test planning -> test case design -> environment setup -> test execution -> defect reporting/retest -> test closure.

| STLC phase | ShopEase artefact |
|---|---|
| Requirement analysis | R-01..R-10 in `test-plan.md` |
| Test planning | `test-plan.md` |
| Test design | `test-scenarios.md`, `test-cases.md`, `tests/` |
| Environment setup | virtualenv, `python -m app.init_db --reset` |
| Execution | `test-execution-report.md` |
| Defect reporting | `bug-reports.md` |
| Closure | summary table, lessons learned in README |

## 4. Positive vs negative testing
Positive = valid input, expected to work (TC-REG-001). Negative = invalid input/conditions, expected to be rejected gracefully (TC-REG-003, TC-CRT-006, TC-CHK-002).

## 5. Scenario vs test case
Scenario: "Verify cart quantity limits" (TS-07). Test cases: quantity 0, 10 and 11 with exact data, steps and expected results (TC-CRT-004..006).

## 6. Equivalence partitioning (EP) and boundary value analysis (BVA)
EP groups inputs expected to behave the same, so you test one representative per group. BVA tests at and next to the edges, where defects cluster.
Cart quantity: partitions `<1` (invalid), `1-10` (valid), `>10` (invalid). Boundaries: 0, 1, 10, 11 (plus type partitions: text, decimal, null).
Password length: 7 (invalid), 8 (valid), 64 (valid), 65 (invalid).

## 7. Types of testing
| Type | Meaning | ShopEase example |
|---|---|---|
| Functional | Does a feature do what the requirement says? | Checkout creates an order |
| Smoke | Is the build stable enough to test? | Section A of `regression-checklist.md` |
| Sanity | Quick focused check after a fix | Re-check TC-CAL-002 after a shipping fix |
| Retesting | Re-run the *failed* case after a fix | Re-run the case behind BUG-001 |
| Regression | Re-run related passing cases to find side effects | Full checklist after changing cart code |
| Exploratory | Simultaneous learning, design and execution, without scripted steps | EXP-01 charter on cart edge cases |

## 8. Defect lifecycle
New -> Assigned -> Open (being fixed) -> Fixed -> Retest -> **Verified/Closed** (or **Reopened** if still failing). Side paths: Rejected (not a defect), Duplicate, Deferred, Cannot reproduce.

## 9. Severity vs priority
See `severity-priority-matrix.md`. Short answer: severity = technical impact; priority = urgency to fix; they can differ (high severity/low priority: crash in a rarely used admin report).

## 10. Expected vs actual result
Expected comes from a requirement or reliable oracle (R-06). Actual is what you observed. A bug exists when they differ and the expected result is right. Always check you are not mis-reading the requirement.

## 11. Test evidence and reproducible bug reports
Evidence: screenshots, Network request/response, console errors, SQL output, logs, with timestamps and build/commit. A good report lets another person reproduce the issue in minutes: exact steps, test data, environment, expected vs actual.

## 12. Useful interview phrases
- "I designed the quantity tests using boundary value analysis: 0, 1, 10, 11."
- "A suspected root cause is a hypothesis until a developer confirms it."
- "Passing automated tests show what I checked, not that the app is bug-free."
