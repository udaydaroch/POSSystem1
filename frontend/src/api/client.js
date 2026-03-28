// In Docker: nginx proxies /api/* to the right service
// In dev (npm run dev): Vite proxies /api to localhost services
const AUTH_URL      = '/api/auth'
const INVENTORY_URL = '/api/inventory'
const POS_URL       = '/api/pos'

function getToken() {
  return localStorage.getItem('prism_token')
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  }
}

async function request(url, options = {}) {
  const res = await fetch(url, options)
  if (res.status === 204) return null

  // Handle non-JSON responses gracefully
  const text = await res.text()
  let data = {}
  try { data = JSON.parse(text) } catch (_) { data = { error: text || `HTTP ${res.status}` } }

  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`)
  return data
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (username, password) =>
    request(`${AUTH_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    }),

  register: (data) =>
    request(`${AUTH_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  me: () =>
    request(`${AUTH_URL}/me`, { headers: authHeaders() })
}

// ── Inventory ─────────────────────────────────────────────────────────────────

export const inventoryApi = {
  getProducts: () =>
    request(`${INVENTORY_URL}/products`, { headers: authHeaders() }),

  getProduct: (id) =>
    request(`${INVENTORY_URL}/products/${id}`, { headers: authHeaders() }),

  createProduct: (data) =>
    request(`${INVENTORY_URL}/products`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data)
    }),

  updateProduct: (id, data) =>
    request(`${INVENTORY_URL}/products/${id}`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(data)
    }),

  adjustStock: (id, delta, reason) =>
    request(`${INVENTORY_URL}/products/${id}/stock?delta=${delta}&reason=${encodeURIComponent(reason || 'Manual adjustment')}`, {
      method: 'PATCH',
      headers: authHeaders()
    }),

  getLowStock: () =>
    request(`${INVENTORY_URL}/products/low-stock`, { headers: authHeaders() })
}

// ── POS ───────────────────────────────────────────────────────────────────────

export const posApi = {
  getSales: () =>
    request(`${POS_URL}/sales`, { headers: authHeaders() }),

  getSale: (id) =>
    request(`${POS_URL}/sale/${id}`, { headers: authHeaders() }),

  createSale: (items, paymentMethod) =>
    request(`${POS_URL}/sale`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ items, paymentMethod })
    }),

  voidSale: (id) =>
    request(`${POS_URL}/sale/${id}/void`, {
      method: 'POST',
      headers: authHeaders()
    })
}
