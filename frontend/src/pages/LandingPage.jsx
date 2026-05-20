import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { vendorApi } from '../lib/api'
import './LandingPage.css'

const CATEGORIES = [
  { code: 'FARM',        label: 'Ferma',       icon: '🌾' },
  { code: 'WINERY',      label: 'Vreshtari',   icon: '🍇' },
  { code: 'AGRITOURISM', label: 'Agriturizma', icon: '🏡' },
  { code: 'RESTAURANT',  label: 'Restorante',  icon: '🍽️' },
]

const STATS = [
  { value: '120+', label: 'Ferma & vreshtari' },
  { value: '8',    label: 'Rajone të Shqipërisë' },
  { value: '3K+',  label: 'Vizitorë çdo muaj' },
  { value: '100%', label: 'Produkte autentike' },
]

const FEATURES = [
  {
    icon: '◎',
    title: 'Zbulo vendet',
    desc: 'Harta interaktive me ferma, vreshtari dhe fshatra turistike në të gjithë Shqipërinë.',
  },
  {
    icon: '◈',
    title: 'Rezervo eksperienca',
    desc: 'Degutime vere, klasa gatimi, netë në fermë — rezervo direkt pa ndërmjetës.',
  },
  {
    icon: '◇',
    title: 'Bli produkte',
    desc: 'Verë, raki, vaj ulliri, djathë artizanal — dërguar deri te dera juaj.',
  },
]

export default function LandingPage() {
  const [vendors, setVendors]   = useState([])
  const [loading, setLoading]   = useState(true)
  const heroRef = useRef(null)

  useEffect(() => {
    vendorApi.list({ limit: 6 })
      .then(r => setVendors(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Parallax on hero text
  useEffect(() => {
    const el = heroRef.current
    if (!el) return
    const onScroll = () => {
      const y = window.scrollY
      el.style.transform = `translateY(${y * 0.3}px)`
      el.style.opacity = Math.max(0, 1 - y / 500)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="landing">

      {/* ── Hero ──────────────────────────────────────────────────── */}
      <section className="hero">
        <div className="hero__bg">
          <div className="hero__bg-circle hero__bg-circle--1" />
          <div className="hero__bg-circle hero__bg-circle--2" />
          <div className="hero__bg-grid" aria-hidden />
        </div>

        <div className="hero__content" ref={heroRef}>
          <span className="hero__eyebrow">Shqipëria Rurale • Autentike • E Pazbuluar</span>
          <h1 className="hero__title">
            Zbulo zemrën<br />
            <em>të fshatit shqiptar</em>
          </h1>
          <p className="hero__desc">
            Ferma, vreshtari dhe eksperienca rurale — rezervo direkt me pronarët.
            Pa ndërmjetës, pa tarifa të fshehura.
          </p>
          <div className="hero__cta">
            <Link to="/explore" className="hero__btn hero__btn--primary">
              Eksplorо tani
            </Link>
            <Link to="/register" className="hero__btn hero__btn--ghost">
              Regjistro fermën tënde →
            </Link>
          </div>
        </div>

        <div className="hero__scroll-hint" aria-hidden>
          <span />
        </div>
      </section>

      {/* ── Stats ─────────────────────────────────────────────────── */}
      <section className="stats">
        <div className="stats__inner">
          {STATS.map(({ value, label }) => (
            <div key={label} className="stats__item">
              <span className="stats__value">{value}</span>
              <span className="stats__label">{label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Categories ────────────────────────────────────────────── */}
      <section className="section">
        <div className="section__inner">
          <div className="section__header">
            <span className="section__tag">Kategoritë</span>
            <h2 className="section__title">Çfarë po kërkon?</h2>
          </div>
          <div className="categories">
            {CATEGORIES.map(({ code, label, icon }) => (
              <Link
                key={code}
                to={`/explore?type=${code}`}
                className="category-card"
              >
                <span className="category-card__icon">{icon}</span>
                <span className="category-card__label">{label}</span>
                <span className="category-card__arrow">→</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── Featured vendors ──────────────────────────────────────── */}
      <section className="section section--parchment">
        <div className="section__inner">
          <div className="section__header">
            <span className="section__tag">Të zgjedhura</span>
            <h2 className="section__title">Vende të spikatura</h2>
            <Link to="/explore" className="section__more">Shiko të gjitha →</Link>
          </div>

          {loading ? (
            <div className="vendors-placeholder">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="vendor-card vendor-card--skeleton" />
              ))}
            </div>
          ) : vendors.length > 0 ? (
            <div className="vendors-grid">
              {vendors.map(v => (
                <VendorCard key={v.id} vendor={v} />
              ))}
            </div>
          ) : (
            <EmptyVendors />
          )}
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────── */}
      <section className="section">
        <div className="section__inner">
          <div className="section__header">
            <span className="section__tag">Si funksionon</span>
            <h2 className="section__title">E thjeshtë nga fillimi deri në fund</h2>
          </div>
          <div className="features">
            {FEATURES.map(({ icon, title, desc }, i) => (
              <div key={title} className="feature">
                <div className="feature__num">{String(i + 1).padStart(2, '0')}</div>
                <div className="feature__icon">{icon}</div>
                <h3 className="feature__title">{title}</h3>
                <p className="feature__desc">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA banner ────────────────────────────────────────────── */}
      <section className="cta-banner">
        <div className="cta-banner__inner">
          <h2 className="cta-banner__title">
            Je pronar ferme apo vreshtarie?
          </h2>
          <p className="cta-banner__desc">
            Bashkohu me FarmaAlb dhe hap dyert e fermës tënde për mysafirë nga e gjithë bota.
          </p>
          <Link to="/register" className="hero__btn hero__btn--primary">
            Regjistro biznesin tënd
          </Link>
        </div>
      </section>

    </div>
  )
}

function VendorCard({ vendor }) {
  const TYPE_LABELS = {
    FARM: 'Fermë', WINERY: 'Vreshtari',
    AGRITOURISM: 'Agriturizma', RESTAURANT: 'Restorant',
  }
  return (
    <Link to={`/vendors/${vendor.id}`} className="vendor-card">
      <div className="vendor-card__img-wrap">
        <div className="vendor-card__img-placeholder">
          {vendor.name.charAt(0)}
        </div>
        <span className="vendor-card__type">
          {TYPE_LABELS[vendor.type] || vendor.type}
        </span>
      </div>
      <div className="vendor-card__body">
        <h3 className="vendor-card__name">{vendor.name}</h3>
        {vendor.region && (
          <p className="vendor-card__region">◎ {vendor.region}</p>
        )}
        {vendor.description && (
          <p className="vendor-card__desc">
            {vendor.description.slice(0, 90)}{vendor.description.length > 90 ? '…' : ''}
          </p>
        )}
        <span className="vendor-card__cta">Shiko më shumë →</span>
      </div>
    </Link>
  )
}

function EmptyVendors() {
  return (
    <div className="empty-vendors">
      <span className="empty-vendors__icon">◎</span>
      <p>Nuk ka ferma të regjistruara ende.</p>
      <Link to="/register" className="hero__btn hero__btn--primary" style={{ marginTop: 16 }}>
        Bëhu i pari
      </Link>
    </div>
  )
}