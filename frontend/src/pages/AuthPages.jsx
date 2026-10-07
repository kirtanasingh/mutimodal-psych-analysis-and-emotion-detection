import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { Activity, ArrowRight } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

function AuthShell({ title, subtitle, children, footer }) {
  return <main className="auth-page">
    <div className="auth-brand"><span className="brand-mark"><Activity size={20} /></span><span>Clinical Workspace</span></div>
    <section className="auth-card">
      <span className="eyebrow">Secure clinical workspace</span>
      <h1>{title}</h1><p className="auth-subtitle">{subtitle}</p>
      {children}
      <div className="auth-footer">{footer}</div>
    </section>
    <p className="auth-disclaimer">Designed for thoughtful, consent-based care.</p>
  </main>
}

export function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('psychologist@example.com')
  const [password, setPassword] = useState('devpassword123')
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault(); setError('')
    try { await login(email, password); navigate('/') } catch (err) { setError(err.message) }
  }
  return <AuthShell title="Welcome back" subtitle="Sign in to continue your clinical work."
    footer={<>New here? <Link to="/signup">Create an account <ArrowRight size={14} /></Link></>}>
    <form className="auth-form" onSubmit={submit}>
      <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
      <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
      {error && <p className="error">{error}</p>}
      <button className="button primary full-width">Sign in</button>
    </form>
  </AuthShell>
}

export function Signup() {
  const navigate = useNavigate()
  const { signup } = useAuth()
  const [form, setForm] = useState({ displayName: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  async function submit(event) {
    event.preventDefault(); setError('')
    if (form.password !== form.confirm) { setError('Passwords do not match'); return }
    try { await signup(form.displayName, form.email, form.password); navigate('/') } catch (err) { setError(err.message) }
  }
  return <AuthShell title="Create your workspace" subtitle="A focused home for patient-centered session analysis."
    footer={<>Already have an account? <Link to="/login">Sign in <ArrowRight size={14} /></Link></>}>
    <form className="auth-form" onSubmit={submit}>
      <label>Your name<input value={form.displayName} onChange={(event) => setForm({ ...form, displayName: event.target.value })} required /></label>
      <label>Email<input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required /></label>
      <label>Password<input type="password" minLength="8" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required /></label>
      <label>Confirm password<input type="password" value={form.confirm} onChange={(event) => setForm({ ...form, confirm: event.target.value })} required /></label>
      {error && <p className="error">{error}</p>}
      <button className="button primary full-width">Create account</button>
    </form>
  </AuthShell>
}
