import { useState, useEffect } from 'react'
import { posApi } from '../api/client'
import './SalesPage.css'

export default function SalesPage() {
  const [sales, setSales] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)
  const [voiding, setVoiding] = useState(null)
  const [filter, setFilter] = useState('ALL')

  const load = () => {
    setLoading(true)
    posApi.getSales().then(s => setSales(Array.isArray(s) ? s : [])).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleVoid = async (sale) => {
    if (!confirm(`Void sale ${sale.referenceNumber}? This will reinstate stock.`)) return
    setVoiding(sale.id)
    try {
      await posApi.voidSale(sale.id)
      load()
    } catch (err) {
      alert(err.message)
    } finally {
      setVoiding(null)
    }
  }

  const fmt = n => `$${Number(n).toFixed(2)}`
  const fmtDate = d => new Date(d).toLocaleString('en-NZ', { dateStyle:'medium', timeStyle:'short' })

  const filtered = filter === 'ALL' ? sales : sales.filter(s => s.status === filter)
  const completedTotal = sales.filter(s => s.status === 'COMPLETED').reduce((sum, s) => sum + Number(s.total), 0)

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Sales History</div>
          <div style={{ fontSize:13, color:'var(--muted)', marginTop:4 }}>
            {sales.filter(s => s.status === 'COMPLETED').length} completed · Total {fmt(completedTotal)}
          </div>
        </div>
        <div style={{ display:'flex', gap:6 }}>
          {['ALL','COMPLETED','VOIDED'].map(f => (
            <button
              key={f}
              className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ color:'var(--muted)', display:'flex', gap:10, alignItems:'center' }}>
          <span className="spinner" /> Loading sales...
        </div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign:'center', color:'var(--dimmed)', padding:'48px 24px' }}>
          No sales found
        </div>
      ) : (
        <div className="sales-list">
          {filtered.map(sale => (
            <div key={sale.id} className="sale-card card">
              <div className="sale-card-head" onClick={() => setExpanded(expanded === sale.id ? null : sale.id)}>
                <div className="sale-card-left">
                  <div className="sale-card-ref">{sale.referenceNumber}</div>
                  <div className="sale-card-meta">
                    {fmtDate(sale.createdAt)} · {sale.cashierUsername} · {sale.paymentMethod}
                  </div>
                </div>
                <div className="sale-card-right">
                  <div className="sale-card-total">{fmt(sale.total)}</div>
                  <div style={{ display:'flex', gap:8, alignItems:'center' }}>
                    <span className={`badge ${sale.status === 'COMPLETED' ? 'badge-green' : sale.status === 'VOIDED' ? 'badge-red' : 'badge-gray'}`}>
                      {sale.status}
                    </span>
                    <span style={{ color:'var(--dimmed)', fontSize:16 }}>
                      {expanded === sale.id ? '▲' : '▼'}
                    </span>
                  </div>
                </div>
              </div>

              {expanded === sale.id && (
                <div className="sale-card-body fade-in">
                  <div className="sale-items">
                    {sale.lineItems?.map((item, i) => (
                      <div key={i} className="sale-item-row">
                        <div className="sale-item-name">{item.productName}</div>
                        <div className="sale-item-sku">{item.sku}</div>
                        <div className="sale-item-qty">× {item.quantity}</div>
                        <div className="sale-item-price">{fmt(item.unitPrice)} each</div>
                        <div className="sale-item-total">{fmt(item.lineTotal)}</div>
                      </div>
                    ))}
                  </div>
                  <div className="sale-breakdown">
                    <div className="bd-row"><span>Subtotal (ex. GST)</span><span>{fmt(sale.subtotal)}</span></div>
                    <div className="bd-row"><span>GST (15%)</span><span>{fmt(sale.taxAmount)}</span></div>
                    <div className="bd-row bd-total"><span>Total</span><span>{fmt(sale.total)}</span></div>
                  </div>
                  {sale.status === 'COMPLETED' && (
                    <div style={{ marginTop:16, display:'flex', justifyContent:'flex-end' }}>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleVoid(sale)}
                        disabled={voiding === sale.id}
                      >
                        {voiding === sale.id ? <span className="spinner" /> : 'Void Sale'}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
