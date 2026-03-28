import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Layout.css'

const NAV = [
  { to: '/dashboard', icon: '◈', label: 'Dashboard' },
  { to: '/pos',       icon: '⊕', label: 'POS Terminal' },
  { to: '/inventory', icon: '≡', label: 'Inventory' },
  { to: '/sales',     icon: '◎', label: 'Sales' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className="layout">
      {/* Mobile top bar */}
      <header className="topbar">
        <button className="burger" onClick={() => setMobileOpen(v => !v)}>
          {mobileOpen ? '✕' : '☰'}
        </button>
        <span className="topbar-logo">PRISM</span>
        <span className="topbar-role badge badge-yellow">{user?.role}</span>
      </header>

      {/* Sidebar */}
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`} onClick={() => setMobileOpen(false)}>
        <div className="sidebar-inner" onClick={e => e.stopPropagation()}>
          <div className="sidebar-head">
            <div className="logo">PRISM</div>
            <div className="logo-sub">ERP · POS</div>
          </div>

          <nav className="sidebar-nav">
            {NAV.map(({ to, icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setMobileOpen(false)}
              >
                <span className="nav-icon">{icon}</span>
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="sidebar-foot">
            <div className="user-info">
              <div className="user-name">{user?.username}</div>
              <div className="user-email">{user?.email}</div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {mobileOpen && <div className="overlay" onClick={() => setMobileOpen(false)} />}

      <main className="main-content">
        <div className="content-inner fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
