import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../api/client'
import './LoginPage.css'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState('login')
  const [form, setForm] = useState({ username: '', password: '', email: '', role: 'CASHIER' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleLogin = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      await authApi.register(form)
      await login(form.username, form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-bg">
        <div className="login-grid" />
      </div>

      <div className="login-box fade-in">
        <div className="login-logo">PRISM</div>
        <div className="login-tagline">Enterprise Resource Platform</div>

        <div className="login-tabs">
          <button className={`tab-btn ${tab === 'login' ? 'active' : ''}`} onClick={() => setTab('login')}>Sign in</button>
          <button className={`tab-btn ${tab === 'register' ? 'active' : ''}`} onClick={() => setTab('register')}>Register</button>
        </div>

        {tab === 'login' ? (
          <form onSubmit={handleLogin} className="login-form">
            <div>
              <label className="label">Username</label>
              <input className="input" value={form.username} onChange={set('username')} placeholder="cashier1" required autoFocus />
            </div>
            <div>
              <label className="label">Password</label>
              <input className="input" type="password" value={form.password} onChange={set('password')} placeholder="••••••••" required />
            </div>
            {error && <div className="login-error">{error}</div>}
            <button className="btn btn-primary btn-lg" style={{width:'100%', justifyContent:'center'}} disabled={loading}>
              {loading ? <span className="spinner" /> : 'Sign in →'}
            </button>
            <div className="login-hint">
              Default admin: <code>admin</code> / <code>Admin1234!</code>
            </div>
          </form>
        ) : (
          <form onSubmit={handleRegister} className="login-form">
            <div>
              <label className="label">Username</label>
              <input className="input" value={form.username} onChange={set('username')} placeholder="cashier1" required autoFocus />
            </div>
            <div>
              <label className="label">Email</label>
              <input className="input" type="email" value={form.email} onChange={set('email')} placeholder="you@prism.nz" required />
            </div>
            <div>
              <label className="label">Password</label>
              <input className="input" type="password" value={form.password} onChange={set('password')} placeholder="Min 8 characters" required />
            </div>
            <div>
              <label className="label">Role</label>
              <select className="input" value={form.role} onChange={set('role')}>
                <option value="CASHIER">Cashier</option>
                <option value="MANAGER">Manager</option>
                <option value="ADMIN">Admin</option>
              </select>
            </div>
            {error && <div className="login-error">{error}</div>}
            <button className="btn btn-primary btn-lg" style={{width:'100%', justifyContent:'center'}} disabled={loading}>
              {loading ? <span className="spinner" /> : 'Create account →'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
