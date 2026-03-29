import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { posApi, inventoryApi } from '../api/client'
import { useAuth } from '../context/AuthContext'
import './DashboardPage.css'

function StatCard({ label, value, sub, accent, onClick }) {
  return (
    <div className={`stat-card card ${onClick ? 'clickable' : ''}`} onClick={onClick}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={accent ? { color: accent } : {}}>{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [sales, setSales] = useState([])
  const [products, setProducts] = useState([])
  const [lowStock, setLowStock] = useState([])
  const [loading, setLoading] = useState(true)

  const canManage = user?.role === 'MANAGER' || user?.role === 'ADMIN'

  useEffect(() => {
    Promise.all([
      posApi.getSales().catch(() => []),
      inventoryApi.getProducts().catch(() => []),
      canManage ? inventoryApi.getLowStock().catch(() => []) : Promise.resolve([]),
    ]).then(([s, p, l]) => {
      setSales(Array.isArray(s) ? s : [])
      setProducts(Array.isArray(p) ? p : [])
      setLowStock(Array.isArray(l) ? l : [])
    }).finally(() => setLoading(false))
  }, [])

  const completed = sales.filter(s => s.status === 'COMPLETED')
  const todayTotal = completed.reduce((sum, s) => sum + Number(s.total || 0), 0)
  const recentSales = completed.slice(0, 5)

  const fmt = (n) => `$${Number(n).toFixed(2)}`
  const fmtNZD = (n) => new Intl.NumberFormat('en-NZ', { style: 'currency', currency: 'NZD' }).format(n)

  if (loading) return (
    <div style={{ display:'flex', alignItems:'center', gap:12, padding:'40px 0', color:'var(--muted)' }}>
      <span className="spinner" /> Loading dashboard...
    </div>
  )

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="page-title">Dashboard</div>
          <div style={{ color:'var(--muted)', fontSize:13, marginTop:4 }}>
            Welcome back, <span style={{ color:'var(--accent)' }}>{user?.username}</span>
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/pos')}>
          ⊕ New Sale
        </button>
      </div>

      <div className="stats-grid">
        <StatCard
          label="Total Sales (all time)"
          value={fmtNZD(todayTotal)}
          sub={`${completed.length} transactions`}
          accent="var(--accent)"
          onClick={() => navigate('/sales')}
        />
        <StatCard
          label="Products in Catalogue"
          value={products.length}
          sub={canManage ? `${lowStock.length} low stock` : undefined}
          onClick={() => navigate('/inventory')}
        />
        <StatCard
          label="Voided Transactions"
          value={sales.filter(s => s.status === 'VOIDED').length}
          sub="All time"
        />
        <StatCard
          label="Avg. Sale Value"
          value={completed.length ? fmtNZD(todayTotal / completed.length) : '$0.00'}
          sub="Per transaction"
          accent="var(--accent2)"
        />
      </div>

      <div className="dash-grid">
        {/* Recent Sales */}
        <div className="card">
          <div className="section-head">
            <span>Recent Sales</span>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/sales')}>View all</button>
          </div>
          {recentSales.length === 0 ? (
            <div className="empty-state">No sales yet — <button className="link-btn" onClick={() => navigate('/pos')}>make your first sale</button></div>
          ) : (
            <div className="sale-list">
              {recentSales.map(sale => (
                <div key={sale.id} className="sale-row">
                  <div>
                    <div className="sale-ref">{sale.referenceNumber}</div>
                    <div className="sale-meta">{sale.cashierUsername} · {sale.paymentMethod}</div>
                  </div>
                  <div style={{ textAlign:'right' }}>
                    <div className="sale-total">{fmt(sale.total)}</div>
                    <div className="sale-gst">incl. {fmt(sale.taxAmount)} GST</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Low Stock Alerts */}
        {canManage && <div className="card">
          <div className="section-head">
            <span>Stock Alerts</span>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/inventory')}>Manage</button>
          </div>
          {lowStock.length === 0 ? (
            <div className="empty-state" style={{ color:'var(--accent2)' }}>✓ All stock levels healthy</div>
          ) : (
            <div className="stock-list">
              {lowStock.map(p => (
                <div key={p.id} className="stock-row">
                  <div>
                    <div className="stock-name">{p.name}</div>
                    <div className="stock-sku">{p.sku}</div>
                  </div>
                  <div className={`badge ${p.stockLevel === 0 ? 'badge-red' : 'badge-yellow'}`}>
                    {p.stockLevel} left
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>}
      </div>
    </div>
  )
}
