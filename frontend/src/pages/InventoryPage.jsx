import { useState, useEffect } from 'react'
import { inventoryApi } from '../api/client'
import { useAuth } from '../context/AuthContext'
import './InventoryPage.css'

const CATEGORIES = ['ELECTRONICS','APPLIANCES','COMPUTERS','PHONES','ACCESSORIES','TV_AUDIO','GAMING','OTHER']

const EMPTY_FORM = { name:'', sku:'', description:'', category:'ELECTRONICS', price:'', stockLevel:'', lowStockThreshold:'5' }

export default function InventoryPage() {
  const { user } = useAuth()
  const canManage = user?.role === 'MANAGER' || user?.role === 'ADMIN'
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [stockModal, setStockModal] = useState(null)
  const [stockDelta, setStockDelta] = useState('')
  const [stockReason, setStockReason] = useState('')

  const load = () => {
    setLoading(true)
    inventoryApi.getProducts()
      .then(p => setProducts(Array.isArray(p) ? p : []))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true); setError('')
    try {
      await inventoryApi.createProduct({
        ...form,
        price: parseFloat(form.price),
        stockLevel: parseInt(form.stockLevel),
        lowStockThreshold: parseInt(form.lowStockThreshold)
      })
      setShowForm(false)
      setForm(EMPTY_FORM)
      load()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleStockAdjust = async () => {
    const delta = parseInt(stockDelta)
    if (isNaN(delta) || delta === 0) return
    try {
      await inventoryApi.adjustStock(stockModal.id, delta, stockReason || 'Manual adjustment')
      setStockModal(null); setStockDelta(''); setStockReason('')
      load()
    } catch (err) {
      alert(err.message)
    }
  }

  const filtered = products.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.sku.toLowerCase().includes(search.toLowerCase())
  )

  const fmt = n => `$${Number(n).toFixed(2)}`

  return (
    <div>
      <div className="page-header">
        <div className="page-title">Inventory</div>
        {canManage && (
          <button className="btn btn-primary" onClick={() => { setShowForm(true); setError('') }}>
            + Add Product
          </button>
        )}
      </div>

      <input
        className="input"
        placeholder="Search by name or SKU..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{ marginBottom: 20, maxWidth: 400 }}
      />

      {/* Add product form */}
      {canManage && showForm && (
        <div className="form-overlay" onClick={() => setShowForm(false)}>
          <div className="form-card card fade-in" onClick={e => e.stopPropagation()}>
            <div className="form-head">
              <span>Add Product</span>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowForm(false)}>✕</button>
            </div>
            <form onSubmit={handleSave} className="product-form">
              <div className="form-row">
                <div>
                  <label className="label">Product Name</label>
                  <input className="input" value={form.name} onChange={set('name')} placeholder='Samsung 55" TV' required />
                </div>
                <div>
                  <label className="label">SKU</label>
                  <input className="input" value={form.sku} onChange={set('sku')} placeholder="SAM-TV-55" required />
                </div>
              </div>
              <div>
                <label className="label">Description</label>
                <input className="input" value={form.description} onChange={set('description')} placeholder="Optional description" />
              </div>
              <div className="form-row">
                <div>
                  <label className="label">Category</label>
                  <select className="input" value={form.category} onChange={set('category')}>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c.replace('_',' ')}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Price (incl. GST)</label>
                  <input className="input" type="number" step="0.01" min="0.01" value={form.price} onChange={set('price')} placeholder="999.00" required />
                </div>
              </div>
              <div className="form-row">
                <div>
                  <label className="label">Stock Level</label>
                  <input className="input" type="number" min="0" value={form.stockLevel} onChange={set('stockLevel')} placeholder="10" required />
                </div>
                <div>
                  <label className="label">Low Stock Alert At</label>
                  <input className="input" type="number" min="0" value={form.lowStockThreshold} onChange={set('lowStockThreshold')} placeholder="5" />
                </div>
              </div>
              {error && <div className="inv-error">{error}</div>}
              <div style={{ display:'flex', gap:10, justifyContent:'flex-end' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? <span className="spinner" /> : 'Save Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Stock adjustment modal */}
      {stockModal && (
        <div className="form-overlay" onClick={() => setStockModal(null)}>
          <div className="form-card card fade-in" style={{ maxWidth: 360 }} onClick={e => e.stopPropagation()}>
            <div className="form-head">
              <span>Adjust Stock</span>
              <button className="btn btn-ghost btn-sm" onClick={() => setStockModal(null)}>✕</button>
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontWeight:500 }}>{stockModal.name}</div>
              <div style={{ color:'var(--muted)', fontSize:12, marginTop:4 }}>Current stock: <strong style={{ color:'var(--accent)' }}>{stockModal.stockLevel}</strong></div>
            </div>
            <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
              <div>
                <label className="label">Delta (+ to add, − to remove)</label>
                <input className="input" type="number" value={stockDelta} onChange={e => setStockDelta(e.target.value)} placeholder="+10 or -3" autoFocus />
              </div>
              <div>
                <label className="label">Reason</label>
                <input className="input" value={stockReason} onChange={e => setStockReason(e.target.value)} placeholder="e.g. New delivery, Damaged goods" />
              </div>
              <button className="btn btn-primary" onClick={handleStockAdjust} disabled={!stockDelta}>
                Apply Adjustment
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ color:'var(--muted)', display:'flex', gap:10, alignItems:'center' }}>
          <span className="spinner" /> Loading products...
        </div>
      ) : (
        <div className="inv-table-wrap">
          <table className="inv-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>SKU</th>
                <th>Category</th>
                <th>Price</th>
                <th>Stock</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={7} style={{ textAlign:'center', color:'var(--dimmed)', padding:'32px 0' }}>
                  {products.length === 0 ? 'No products yet — add your first product above' : 'No products match your search'}
                </td></tr>
              ) : filtered.map(p => (
                <tr key={p.id}>
                  <td>
                    <div className="prod-name">{p.name}</div>
                    {p.description && <div className="prod-desc">{p.description}</div>}
                  </td>
                  <td><span className="mono-badge">{p.sku}</span></td>
                  <td><span className="badge badge-gray">{p.category?.replace('_',' ')}</span></td>
                  <td className="price-cell">{fmt(p.price)}</td>
                  <td>
                    <span className={`stock-num ${p.stockLevel === 0 ? 'zero' : p.stockLevel <= p.lowStockThreshold ? 'low' : ''}`}>
                      {p.stockLevel}
                    </span>
                  </td>
                  <td>
                    {p.stockLevel === 0
                      ? <span className="badge badge-red">Out of stock</span>
                      : p.stockLevel <= p.lowStockThreshold
                        ? <span className="badge badge-yellow">Low stock</span>
                        : <span className="badge badge-green">In stock</span>
                    }
                  </td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={() => {
                      setStockModal(p); setStockDelta(''); setStockReason('')
                    }}>Adjust stock</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
