import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Alert from '../components/ui/Alert'
import './AuthPage.css'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate  = useNavigate()
  const location  = useLocation()
  const from      = location.state?.from || '/dashboard'

  const [form, setForm]       = useState({ email: '', password: '' })
  const [errors, setErrors]   = useState({})
  const [apiError, setApiError] = useState('')
  const [loading, setLoading] = useState(false)

  const validate = () => {
    const e = {}
    if (!form.email)    e.email    = 'Email-i është i detyrueshëm'
    if (!form.password) e.password = 'Fjalëkalimi është i detyrueshëm'
    return e
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: '' }))
    if (apiError) setApiError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setLoading(true)
    try {
      await login(form.email, form.password)
      navigate(from, { replace: true })
    } catch (err) {
      const msg = err.response?.data?.detail
      setApiError(
        typeof msg === 'string'
          ? msg
          : 'Kredencialet janë të gabuara. Provo përsëri.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      {/* Left panel — decorative */}
      <div className="auth-page__panel" aria-hidden>
        <div className="auth-page__panel-content">
          <p className="auth-page__panel-quote">
            "Toka shqiptare rrit<br />
            <em>të mirat e vërteta.</em>"
          </p>
          <div className="auth-page__panel-dots">
            <span /><span /><span />
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="auth-page__form-wrap">
        <div className="auth-page__form-inner">
          {/* Logo */}
          <Link to="/" className="auth-page__logo">
            <span className="auth-page__logo-icon">⊕</span>
            <span className="auth-page__logo-name">FarmaAlb</span>
          </Link>

          <div className="auth-page__header">
            <h1 className="auth-page__title">Mirë se erdhe</h1>
            <p className="auth-page__subtitle">
              Hyr për të eksploruar fermat dhe vreshtaritë shqiptare
            </p>
          </div>

          {apiError && (
            <Alert type="error" onDismiss={() => setApiError('')}>
              {apiError}
            </Alert>
          )}

          <form className="auth-page__fields" onSubmit={handleSubmit} noValidate>
            <Input
              label="Email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              error={errors.email}
              placeholder="emri@shembull.al"
              required
              autoComplete="email"
              autoFocus
            />
            <Input
              label="Fjalëkalimi"
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              error={errors.password}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />

            <div className="auth-page__forgot">
              <Link to="/forgot-password">Harruat fjalëkalimin?</Link>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={loading}
            >
              Hyr në llogari
            </Button>
          </form>

          <p className="auth-page__switch">
            Nuk keni llogari?{' '}
            <Link to="/register">Regjistrohu falas</Link>
          </p>
        </div>
      </div>
    </div>
  )
}