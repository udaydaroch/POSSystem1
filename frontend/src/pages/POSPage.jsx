import { useState, useEffect } from 'react'
import { inventoryApi, posApi } from '../api/client'
import './POSPage.css'

const PAYMENT_METHODS = ['EFTPOS', 'CASH', 'CREDIT_CARD']

export default function POSPage() {
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [search, setSearch] = useState('')
  const [payment, setPayment] = useState('EFTPOS')
  const [loading, setLoading] = useState(false)
  const [receipt, setReceipt] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    inventoryApi.getProducts().then(p => setProducts(Array.isArray(p) ? p : []))
  }, [])

  const filtered = products.filter(p =>
    p.active && (
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku.toLowerCase().includes(search.toLowerCase())
    )
  )

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(i => i.product.id === product.id)
      if (existing) {
        if (existing.qty >= product.stockLevel) return prev
        return prev.map(i => i.product.id === product.id ? { ...i, qty: i.qty + 1 } : i)
      }
      return [...prev, { product, qty: 1 }]
    })
    setError('')
  }

  const removeFromCart = (id) => setCart(prev => prev.filter(i => i.product.id !== id))

  const updateQty = (id, qty) => {
    const n = parseInt(qty)
    if (isNaN(n) || n < 1) return
    const item = cart.find(i => i.product.id === id)
    if (n > item.product.stockLevel) return
    setCart(prev => prev.map(i => i.product.id === id ? { ...i, qty: n } : i))
  }

  const subtotalExGST = cart.reduce((sum, i) => {
    const lineTotal = i.product.price * i.qty
    return sum + lineTotal / 1.15
  }, 0)
  const gst = cart.reduce((sum, i) => {
    const lineTotal = i.product.price * i.qty
    return sum + (lineTotal * 0.15) / 1.15
  }, 0)
  const total = cart.reduce((sum, i) => sum + i.product.price * i.qty, 0)

  const fmt = (n) => `$${Number(n).toFixed(2)}`

  const processPayment = async () => {
    if (cart.length === 0) return
    setLoading(true); setError('')
    try {
      const items = cart.map(i => ({ productId: i.product.id, quantity: i.qty }))
      const sale = await posApi.createSale(items, payment)
      setReceipt(sale)
      setCart([])
      setSearch('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (receipt) {
    return (
      <div className="receipt-screen fade-in">
        <div className="receipt-card card">
          <div className="receipt-tick">✓</div>
          <div className="receipt-title">Sale Complete</div>
          <div className="receipt-ref">{receipt.referenceNumber}</div>

          <div className="receipt-items">
            {receipt.lineItems?.map((item, i) => (
              <div key={i} className="receipt-item">
                <span>{item.productName} × {item.quantity}</span>
                <span>{fmt(item.lineTotal)}</span>
              </div>
            ))}
          </div>

          <div className="receipt-totals">
            <div className="receipt-row"><span>Subtotal (ex. GST)</span><span>{fmt(receipt.subtotal)}</span></div>
            <div className="receipt-row"><span>GST (15%)</span><span>{fmt(receipt.taxAmount)}</span></div>
            <div className="receipt-row total"><span>Total</span><span>{fmt(receipt.total)}</span></div>
            <div className="receipt-row"><span>Payment</span><span>{receipt.paymentMethod}</span></div>
          </div>

          <button className="btn btn-primary btn-lg" style={{ width:'100%', justifyContent:'center' }}
            onClick={() => setReceipt(null)}>
            New Sale →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="pos-layout">
      {/* Left: Product catalogue */}
      <div className="pos-catalogue">
        <div className="page-header">
          <div className="page-title">POS Terminal</div>
        </div>

        <input
          className="input"
          placeholder="Search products or SKU..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ marginBottom: 16 }}
          autoFocus
        />

        <div className="product-grid">
          {filtered.length === 0 ? (
            <div style={{ color:'var(--dimmed)', fontSize:13, gridColumn:'1/-1', padding:'24px 0' }}>
              {products.length === 0 ? 'No products yet — add some in Inventory' : 'No products match your search'}
            </div>
          ) : filtered.map(product => (
            <button
              key={product.id}
              className={`product-tile ${product.stockLevel === 0 ? 'out-of-stock' : ''}`}
              onClick={() => product.stockLevel > 0 && addToCart(product)}
              disabled={product.stockLevel === 0}
            >
              <div className="product-category">{product.category}</div>
              <div className="product-name">{product.name}</div>
              <div className="product-sku">{product.sku}</div>
              <div className="product-price">{fmt(product.price)}</div>
              <div className={`product-stock ${product.stockLevel <= product.lowStockThreshold ? 'low' : ''}`}>
                {product.stockLevel === 0 ? 'Out of stock' : `${product.stockLevel} in stock`}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Right: Cart */}
      <div className="pos-cart">
        <div className="cart-header">
          <span>Cart</span>
          {cart.length > 0 && (
            <button className="btn btn-ghost btn-sm" onClick={() => setCart([])}>Clear</button>
          )}
        </div>

        <div className="cart-items">
          {cart.length === 0 ? (
            <div className="cart-empty">Tap a product to add it</div>
          ) : cart.map(({ product, qty }) => (
            <div key={product.id} className="cart-item">
              <div className="cart-item-info">
                <div className="cart-item-name">{product.name}</div>
                <div className="cart-item-price">{fmt(product.price)} each</div>
              </div>
              <div className="cart-item-controls">
                <button className="qty-btn" onClick={() => qty === 1 ? removeFromCart(product.id) : updateQty(product.id, qty - 1)}>−</button>
                <input
                  className="qty-input"
                  type="number"
                  value={qty}
                  min={1}
                  max={product.stockLevel}
                  onChange={e => updateQty(product.id, e.target.value)}
                />
                <button className="qty-btn" onClick={() => updateQty(product.id, qty + 1)} disabled={qty >= product.stockLevel}>+</button>
              </div>
              <div className="cart-item-total">{fmt(product.price * qty)}</div>
              <button className="remove-btn" onClick={() => removeFromCart(product.id)}>✕</button>
            </div>
          ))}
        </div>

        <div className="cart-summary">
          <div className="summary-row"><span>Subtotal (ex. GST)</span><span>{fmt(subtotalExGST)}</span></div>
          <div className="summary-row"><span>GST 15%</span><span>{fmt(gst)}</span></div>
          <div className="summary-row total-row"><span>Total</span><span>{fmt(total)}</span></div>

          <div className="payment-select">
            {PAYMENT_METHODS.map(m => (
              <button
                key={m}
                className={`pay-method ${payment === m ? 'active' : ''}`}
                onClick={() => setPayment(m)}
              >
                {m === 'EFTPOS' ? '💳' : m === 'CASH' ? '💵' : '🏦'} {m}
              </button>
            ))}
          </div>

          {error && <div className="cart-error">{error}</div>}

          <button
            className="btn btn-primary btn-lg"
            style={{ width:'100%', justifyContent:'center' }}
            disabled={cart.length === 0 || loading}
            onClick={processPayment}
          >
            {loading ? <span className="spinner" /> : `Charge ${fmt(total)}`}
          </button>
        </div>
      </div>
    </div>
  )
}
