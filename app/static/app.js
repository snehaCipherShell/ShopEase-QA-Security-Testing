"use strict";
const $ = (id) => document.getElementById(id);
const fmt = (n) => Number(n).toFixed(2);

async function api(method, path, body) {
  const opts = { method, headers: {}, credentials: "same-origin" };
  if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  const res = await fetch("/api" + path, opts);
  let data = null;
  try { data = await res.json(); } catch (e) { /* non-JSON body */ }
  return { status: res.status, ok: res.ok, data };
}
function show(text, isError) { const el = $("message"); el.textContent = text; el.className = isError ? "error" : "success"; }
function errText(r) { return (r.data && r.data.error && r.data.error.message) || ("Request failed (" + r.status + ")"); }
function el(tag, text, attrs) { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; Object.assign(e, attrs || {}); return e; }

async function refreshUser() {
  const r = await api("GET", "/auth/me");
  const loggedIn = r.ok;
  $("whoami").textContent = loggedIn ? "Logged in as " + r.data.username : "Not logged in";
  $("logout-btn").hidden = !loggedIn;
  if (loggedIn) { await Promise.all([loadCart(), loadOrders()]); } else { renderCart(null); $("order-list").replaceChildren(); }
}

async function loadProducts(q) {
  const r = await api("GET", "/products" + (q ? "?q=" + encodeURIComponent(q) : ""));
  const list = $("product-list"); list.replaceChildren();
  if (!r.ok) { show(errText(r), true); return; }
  if (r.data.count === 0) { list.appendChild(el("li", "No products found.")); return; }
  r.data.products.forEach((p) => {
    const li = el("li", p.name + " \u2014 " + fmt(p.price) + " ");
    li.appendChild(el("span", p.stock > 0 ? "(" + p.stock + " in stock) " : "(out of stock) ", { className: "muted" }));
    const qty = el("input", undefined, { type: "number", min: 1, max: 10, value: 1, size: 3 }); qty.style.width = "3.5rem";
    const btn = el("button", "Add to cart", { id: "add-" + p.id });
    btn.addEventListener("click", async () => {
      const res = await api("POST", "/cart/items", { product_id: p.id, quantity: Number(qty.value) });
      if (res.ok) { show("Added " + p.name + " to cart.", false); renderCart(res.data); } else { show(errText(res), true); }
    });
    li.append(qty, btn); list.appendChild(li);
  });
}

function renderCart(cart) {
  const body = $("cart-table").tBodies[0]; body.replaceChildren();
  if (!cart) { $("cart-subtotal").textContent = "0.00"; return; }
  cart.items.forEach((it) => {
    const tr = el("tr");
    const qty = el("input", undefined, { type: "number", min: 1, max: 10, value: it.quantity }); qty.style.width = "3.5rem";
    qty.addEventListener("change", async () => {
      const res = await api("PUT", "/cart/items/" + it.product_id, { quantity: Number(qty.value) });
      if (res.ok) { renderCart(res.data); show("Cart updated.", false); } else { show(errText(res), true); loadCart(); }
    });
    const rm = el("button", "Remove");
    rm.addEventListener("click", async () => {
      const res = await api("DELETE", "/cart/items/" + it.product_id);
      if (res.ok) { renderCart(res.data); show("Item removed.", false); } else { show(errText(res), true); }
    });
    [el("td", it.name), el("td", fmt(it.unit_price)), el("td"), el("td", fmt(it.line_total)), el("td")].forEach((td, i) => {
      if (i === 2) td.appendChild(qty); if (i === 4) td.appendChild(rm); tr.appendChild(td);
    });
    body.appendChild(tr);
  });
  $("cart-subtotal").textContent = fmt(cart.subtotal);
}
async function loadCart() { const r = await api("GET", "/cart"); if (r.ok) renderCart(r.data); }

async function loadOrders() {
  const r = await api("GET", "/orders"); const list = $("order-list"); list.replaceChildren();
  if (!r.ok) return;
  if (r.data.count === 0) { list.appendChild(el("li", "No orders yet.")); return; }
  r.data.orders.forEach((o) => {
    const li = el("li", "Order #" + o.id + " \u2014 " + o.status + " \u2014 total " + fmt(o.total) + " (" + o.item_count + " items) ");
    if (o.status === "PLACED") {
      const b = el("button", "Cancel");
      b.addEventListener("click", async () => {
        const res = await api("POST", "/orders/" + o.id + "/cancel");
        show(res.ok ? "Order cancelled." : errText(res), !res.ok); loadOrders(); loadProducts($("search-input").value);
      });
      li.appendChild(b);
    }
    list.appendChild(li);
  });
}

$("register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const r = await api("POST", "/auth/register", { username: $("reg-username").value, email: $("reg-email").value, password: $("reg-password").value });
  if (r.ok) { show("Registration successful. You can now log in.", false); e.target.reset(); } else {
    const f = r.data && r.data.error && r.data.error.fields;
    show(f ? errText(r) + " " + Object.entries(f).map(([k, v]) => k + ": " + v).join("; ") : errText(r), true);
  }
});
$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const r = await api("POST", "/auth/login", { username: $("login-username").value, password: $("login-password").value });
  if (r.ok) { show("Logged in.", false); e.target.reset(); await refreshUser(); } else { show(errText(r), true); }
});
$("logout-btn").addEventListener("click", async () => { const r = await api("POST", "/auth/logout"); show(r.ok ? "Logged out." : errText(r), !r.ok); await refreshUser(); });
$("search-form").addEventListener("submit", (e) => { e.preventDefault(); loadProducts($("search-input").value); });
$("checkout-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const r = await api("POST", "/checkout", { shipping_name: $("ship-name").value, shipping_address: $("ship-address").value, payment_method: "SIMULATED" });
  if (r.ok) { show("Order #" + r.data.id + " placed. Total " + fmt(r.data.total) + " (simulated payment).", false); renderCart({ items: [], subtotal: 0 }); loadOrders(); loadProducts($("search-input").value); } else { show(errText(r), true); }
});

loadProducts(""); refreshUser();
