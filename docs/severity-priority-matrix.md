# Severity vs Priority Matrix

- **Severity** = how bad the defect is *technically/for the user* (impact on the system). Usually set by QA.
- **Priority** = how soon it should be fixed (business urgency). Usually set by the product owner / team lead, with QA input.

They are related but independent. **Final ratings always depend on actual impact, how often it happens, who is affected and the business context** - the examples below are illustrations, not fixed rules.

| Severity | Typical meaning |
|---|---|
| Critical | Crash, data loss, security breach, core flow impossible, no workaround |
| High | Major feature broken or wrong money/data, workaround is hard |
| Medium | Feature partly wrong, workaround exists |
| Low | Cosmetic, minor wording, rare edge case |

| Priority | Typical meaning |
|---|---|
| High | Fix immediately / before release |
| Medium | Fix in the current or next cycle |
| Low | Fix when time allows |

## Examples (ShopEase, hypothetical unless stated)
| # | Defect | Severity | Priority | Why |
|---|---|---|---|---|
| 1 | Checkout charges the wrong total | High | High | Wrong money on the core revenue flow |
| 2 | Another user's order is readable by changing the ID in the URL | High (could be Critical if sensitive data) | High | Broken access control; privacy impact |
| 3 | Typo in the checkout button label | Low | Medium | Cosmetic, but highly visible on the payment page; a brand-sensitive team may fix it quickly |
| 4 | Crash on a rarely used admin report | High | Low | Serious technically, but almost nobody uses it, so urgency is low |
| 5 | Company logo misspelled on the home page | Low | High | No functional impact, but embarrassing before a launch |
| 6 | Search returns no results for a product written in capitals | Medium | Medium | Feature partly wrong; user can retype |
| 7 | Server banner reveals framework version (BUG-001, real, fixed) | Low | Low | Minor information disclosure on a local training app |
| 8 | Out-of-stock product can be ordered, causing negative stock | Medium | High | Operational problem near launch |

## Quick grid
| | **Priority High** | **Priority Low** |
|---|---|---|
| **Severity High** | Wrong order total; broken access control | Crash in a rarely used admin feature |
| **Severity Low** | Misspelled logo before a launch | Colour shade off by a few percent |

## Tips
- Write the *reason* next to every rating.
- Re-assess when new information appears (for example a "Low" bug that is actually exploitable).
- For security issues, also think about likelihood, required access, and data affected; do not copy scores from tools without understanding them.
