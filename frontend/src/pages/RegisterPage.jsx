import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getErrorMessage } from '../lib/errors'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Alert from '../components/ui/Alert'
import './AuthPage.css'
import './RegisterPage.css'

const LOCALES = [
  { value: 'sq', label: 'Shqip' },
  { value: 'en', label: 'English' },
  { value: 'it', label: 'Italiano' },
]

const STEPS = ['Llogaria', 'Profili', 'Konfirmo']

export default function RegisterPage() {
  const { register, login } = useAuth()
  const navigate = useNavigate()

  const [step, setStep]         = useState(0)
  const [form, setForm]         = useState({
    full_name: '',
    email:     '',
    password:  '',
    confirm:   '',
    locale:    'sq',
  })
  const [errors, setErrors]     = useState({})
  const [apiError, setApiError] = useState('')
  const [loading, setLoading]   = useState(false)

  // ── Field change ──────────────────────────────────────────────────────────
  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: '' }))
    if (apiError) setApiError('')
  }

  // ── Per-step validation ───────────────────────────────────────────────────
  const validateStep = (s) => {
    const e = {}
    if (s === 0) {
      if (!form.email)
        e.email = 'Email-i është i detyrueshëm'
      else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
        e.email = 'Email-i nuk është i vlefshëm'
      if (!form.password)
        e.password = 'Fjalëkalimi është i detyrueshëm'
      else if (form.password.length < 8)
        e.password = 'Fjalëkalimi duhet të ketë të paktën 8 karaktere'
      if (!form.confirm)
        e.confirm = 'Konfirmo fjalëkalimin'
      else if (form.confirm !== form.password)
        e.confirm = 'Fjalëkalimet nuk përputhen'
    }
    if (s === 1) {
      if (!form.full_name.trim())
        e.full_name = 'Emri i plotë është i detyrueshëm'
      else if (form.full_name.trim().length < 3)
        e.full_name = 'Emri duhet të ketë të paktën 3 karaktere'
    }
    return e
  }

  // ── Next step ─────────────────────────────────────────────────────────────
  const handleNext = () => {
    const errs = validateStep(step)
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})
    setStep(s => s + 1)
  }

  // ── Submit ────────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    setLoading(true)
    try {
      await register({
        full_name: form.full_name.trim(),
        email:     form.email,
        password:  form.password,
        locale:    form.locale,
      })
      // Auto-login after register
      await login(form.email, form.password)
      navigate('/', { replace: true })
    } catch (err) {
      setApiError(getErrorMessage(err))
      setStep(0)
    } finally {
      setLoading(false)
    }
  }

  // ── Password strength ─────────────────────────────────────────────────────
  const strength = getPasswordStrength(form.password)

  return (
    <div className="auth-page">

      {/* Left decorative panel */}
      <div className="auth-page__panel auth-page__panel--register" aria-hidden>
        <div className="auth-page__panel-content">
          <div className="reg-panel__steps">
            {STEPS.map((label, i) => (
              <div
                key={label}
                className={`reg-panel__step ${
                  i < step  ? 'reg-panel__step--done'   :
                  i === step ? 'reg-panel__step--active' : ''
                }`}
              >
                <div className="reg-panel__step-dot">
                  {i < step ? '✓' : i + 1}
                </div>
                <span className="reg-panel__step-label">{label}</span>
                {i < STEPS.length - 1 && (
                  <div className="reg-panel__step-line" />
                )}
              </div>
            ))}
          </div>
          <p className="auth-page__panel-quote" style={{ marginTop: 48 }}>
            "Bashkohu me<br />
            <em>komunitetin rural</em><br />
            shqiptar."
          </p>
        </div>
      </div>

      {/* Right form panel */}
      <div className="auth-page__form-wrap">
        <div className="auth-page__form-inner">

          {/* Logo */}
          <Link to="/" className="auth-page__logo">
            <span className="auth-page__logo-icon">⊕</span>
            <span className="auth-page__logo-name">FarmaAlb</span>
          </Link>

          {/* Header */}
          <div className="auth-page__header">
            <h1 className="auth-page__title">Krijo llogarinë</h1>
            <p className="auth-page__subtitle">
              Hapi {step + 1} nga {STEPS.length} — {STEPS[step]}
            </p>
          </div>

          {/* Step progress bar */}
          <div className="reg-progress" role="progressbar"
            aria-valuenow={step + 1} aria-valuemin={1} aria-valuemax={STEPS.length}>
            <div
              className="reg-progress__bar"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>

          {apiError && (
            <Alert type="error" onDismiss={() => setApiError('')}>
              {apiError}
            </Alert>
          )}

          {/* ── Step 0 — Account ── */}
          {step === 0 && (
            <div className="auth-page__fields" key="step0">
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
                placeholder="Të paktën 8 karaktere"
                required
                autoComplete="new-password"
              />

              {/* Password strength */}
              {form.password && (
                <div className="pwd-strength">
                  <div className="pwd-strength__bars">
                    {[0, 1, 2, 3].map(i => (
                      <div
                        key={i}
                        className={`pwd-strength__bar ${
                          i < strength.score ? `pwd-strength__bar--${strength.level}` : ''
                        }`}
                      />
                    ))}
                  </div>
                  <span className={`pwd-strength__label pwd-strength__label--${strength.level}`}>
                    {strength.label}
                  </span>
                </div>
              )}

              <Input
                label="Konfirmo fjalëkalimin"
                name="confirm"
                type="password"
                value={form.confirm}
                onChange={handleChange}
                error={errors.confirm}
                placeholder="Rifut fjalëkalimin"
                required
                autoComplete="new-password"
              />

              <Button
                variant="primary"
                size="lg"
                fullWidth
                onClick={handleNext}
              >
                Vazhdo →
              </Button>
            </div>
          )}

          {/* ── Step 1 — Profile ── */}
          {step === 1 && (
            <div className="auth-page__fields" key="step1">
              <Input
                label="Emri i plotë"
                name="full_name"
                type="text"
                value={form.full_name}
                onChange={handleChange}
                error={errors.full_name}
                placeholder="p.sh. Ardit Kelmendi"
                required
                autoComplete="name"
                autoFocus
              />

              <div className="field">
                <label className="field__label" htmlFor="locale">
                  Gjuha e preferuar
                </label>
                <select
                  id="locale"
                  name="locale"
                  className="field__input field__select"
                  value={form.locale}
                  onChange={handleChange}
                >
                  {LOCALES.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              <div className="reg-nav">
                <Button variant="secondary" size="lg" onClick={() => setStep(0)}>
                  ← Mbrapa
                </Button>
                <Button variant="primary" size="lg" onClick={handleNext}>
                  Vazhdo →
                </Button>
              </div>
            </div>
          )}

          {/* ── Step 2 — Confirm ── */}
          {step === 2 && (
            <div className="auth-page__fields" key="step2">
              <div className="reg-summary">
                <div className="reg-summary__avatar">
                  {form.full_name.trim().charAt(0).toUpperCase() || '?'}
                </div>
                <div className="reg-summary__rows">
                  <div className="reg-summary__row">
                    <span className="reg-summary__key">Emri</span>
                    <span className="reg-summary__val">{form.full_name}</span>
                  </div>
                  <div className="reg-summary__row">
                    <span className="reg-summary__key">Email</span>
                    <span className="reg-summary__val">{form.email}</span>
                  </div>
                  <div className="reg-summary__row">
                    <span className="reg-summary__key">Gjuha</span>
                    <span className="reg-summary__val">
                      {LOCALES.find(l => l.value === form.locale)?.label}
                    </span>
                  </div>
                </div>
              </div>

              <p className="reg-terms">
                Duke klikuar "Krijo llogarinë" pranoni{' '}
                <Link to="/terms">Kushtet e shërbimit</Link> dhe{' '}
                <Link to="/privacy">Politikën e privatësisë</Link> të FarmaAlb.
              </p>

              <div className="reg-nav">
                <Button variant="secondary" size="lg" onClick={() => setStep(1)}>
                  ← Mbrapa
                </Button>
                <Button
                  variant="primary"
                  size="lg"
                  loading={loading}
                  onClick={handleSubmit}
                >
                  Krijo llogarinë ✓
                </Button>
              </div>
            </div>
          )}

          <p className="auth-page__switch">
            Keni llogari?{' '}
            <Link to="/login">Hyr këtu</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

// ── Password strength helper ────────────────────────────────────────────────
function getPasswordStrength(pwd) {
  if (!pwd) return { score: 0, level: 'weak', label: '' }
  let score = 0
  if (pwd.length >= 8)                    score++
  if (pwd.length >= 12)                   score++
  if (/[A-Z]/.test(pwd) && /[0-9]/.test(pwd)) score++
  if (/[^A-Za-z0-9]/.test(pwd))          score++

  if (score <= 1) return { score: 1, level: 'weak',   label: 'E dobët' }
  if (score === 2) return { score: 2, level: 'fair',   label: 'Mesatare' }
  if (score === 3) return { score: 3, level: 'good',   label: 'E mirë' }
  return             { score: 4, level: 'strong', label: 'E fortë' }
}