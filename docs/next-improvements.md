# Next Improvements

## Testing
- [ ] Browser automation (Playwright or Selenium) for registration, cart and checkout flows
- [ ] CI: GitHub Actions workflow running `pytest` on every push
- [ ] Coverage report (`pytest --cov=app`)
- [ ] Concurrency test: two simultaneous checkouts for the last unit of stock
- [ ] Newman (Postman CLI) run in CI
- [ ] Performance smoke test of search with a tool such as Locust (local only)
- [ ] Accessibility checks with browser extensions

## Security (local, authorised only)
- [ ] Add login rate limiting, then write tests proving it
- [ ] CSRF analysis and, if needed, tokens
- [ ] Local HTTPS (self-signed) and `Secure` cookie verification
- [ ] Dependency scanning (`pip-audit`) and static analysis (`bandit`)
- [ ] Practise with an authorised intercepting proxy (e.g. Burp Community or OWASP ZAP) **against your local instance only**
- [ ] Structured security logging and review

## Documentation
- [ ] Add real screenshots and execution results
- [ ] Record a short demo video (optional)
- [ ] Write a retrospective: what bugs the tests found, what they missed
