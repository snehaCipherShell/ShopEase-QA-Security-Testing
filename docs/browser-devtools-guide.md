# Browser Developer Tools for Testers

Open DevTools: `F12` or `Ctrl+Shift+I` (Firefox/Chrome on Kali). Use it **only on your local ShopEase** (`http://127.0.0.1:5000`) or other systems you are authorised to test.

## 1. Elements (Inspector)
Shows the live HTML/CSS. Use it to: check labels, IDs and attributes (`id="register-btn"`); confirm what the user sees vs the DOM; temporarily edit values to test client-side validation (e.g. change `max="10"` on the quantity input to try 99 - the **server must still reject it**, see TC-CRT-006, SEC-PRICE-001). Edits are local to your browser and vanish on reload.

## 2. Console
Shows JavaScript errors and warnings (red entries are worth a bug report if reproducible). You can run small snippets, e.g. `fetch('/api/cart').then(r => r.json()).then(console.log)`.

## 3. Network
Records every request. Click a request to see: **Headers** (method, URL, status, request/response headers, `Set-Cookie`), **Payload** (JSON body sent), **Response** (JSON received), **Timing**. Filter with `Fetch/XHR`. Tick **Preserve log** so entries survive page reloads. Right-click > *Copy as cURL* to reproduce a request in a terminal or attach to a bug.

## 4. Application (Chrome) / Storage (Firefox)
**Cookies > `http://127.0.0.1:5000`**: inspect `shopease_session`: Value (random token), Path, Expires, **HttpOnly**, **Secure**, **SameSite**. After logout the cookie should be removed and the old value should no longer work (SEC-SESS-001). Local/Session storage: ShopEase stores nothing sensitive there - confirm.

## 5. Walkthrough: investigating a wrong cart total
> This is a **teaching scenario**. The current ShopEase build is not known to have this defect; BUG-SIM-001 is a simulated example.

Symptom: cart shows subtotal 39.98 after changing a quantity from 2 to 5 (expected 99.95).
1. **Reproduce and record** exact steps and test data (Wireless Mouse 19.99, quantity 2 -> 5).
2. **Network:** open the `PUT /api/cart/items/1` request. Check *Status* (200?), *Payload* (`{"quantity":5}`?), *Response* (`subtotal`: 99.95 or 39.98?).
3. **Interpret:** if the response says 39.98, the server calculation or data is suspect; if it says 99.95 but the page shows 39.98, the front-end is not using the response. Both are *hypotheses* until confirmed.
4. **Console:** look for JavaScript errors at the moment of the change.
5. **Elements:** is the displayed number in the element `#cart-subtotal` stale? Was the right element updated?
6. **Application:** nothing session-related should differ; confirm you are the intended user (`/api/auth/me`).
7. **Database:** compare with SQL A15 (cart) to see the stored quantity.
8. **Record evidence:** screenshot of the Network response and the page, copy as cURL, SQL output, timestamp, commit.

## 6. Inspect a request and response (step by step)
1. Network tab > clear > tick Preserve log. 2. Perform the action (e.g. Login). 3. Click the `login` entry. 4. Headers: method POST, status 200. 5. Payload: `username`, `password` (visible to *you* because it is your own browser). 6. Response: id, username, role, no hash. 7. Response headers: `Set-Cookie: shopease_session=...; HttpOnly; SameSite=Lax; Path=/; Max-Age=3600`.

## 7. Recording evidence
Name files `TC-ID_description_date.png`, store in `screenshots/`, crop out anything private, include URL bar/time when useful, and **never publish real tokens**: crop or blur cookie values (even though ShopEase data is fictional, building the habit matters).

## 8. Limits of browser evidence
DevTools shows what the *browser* sent and received. It can **suggest** where a problem lives but does not by itself **prove** the root cause: caching, extensions, timing, front-end state and server logic can all look similar. Confirm with a second method (curl/Postman, SQL, server log) and describe uncertainty honestly in the bug report.
