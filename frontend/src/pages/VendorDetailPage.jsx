import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { vendorApi, catalogApi, reviewApi } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/layout/Navbar'
import Spinner from '../components/ui/Spinner'
import './VendorDetailPage.css'

const TYPE_META = {
  FARM:        { label: 'Fermë',       color: '#4a5240', bg: '#eef2ea' },
  WINERY:      { label: 'Vreshtari',   color: '#6b3a2a', bg: '#f5ece8' },
  AGRITOURISM: { label: 'Agriturizma', color: '#2a4a5a', bg: '#e8f2f5' },
  RESTAURANT:  { label: 'Restorant',   color: '#3a3a2a', bg: '#f2f2e8' },
}

const EXP_TYPE_LABELS = {
  TASTING:       'Degustim',
  COOKING_CLASS: 'Workshop Gatimi',
  FARM_STAY:     'Natë në Fermë',
  TOUR:          'Tur Guidat',
  HARVEST:       'Korrje',
}

const CAT_LABELS = {
  WINE:      'Verë',
  OLIVE_OIL: 'Vaj Ulliri',
  CHEESE:    'Djathë',
  RAKIA:     'Raki',
  HONEY:     'Mjaltë',
  OTHER:     'Tjetër',
}

const TABS = ['Eksperienca', 'Produkte', 'Komente']

export default function VendorDetailPage() {
  const { id }       = useParams()
  const { user }     = useAuth()
  const navigate     = useNavigate()

  const [vendor,       setVendor]       = useState(null)
  const [experiences,  setExperiences]  = useState([])
  const [products,     setProducts]     = useState([])
  const [reviews,      setReviews]      = useState([])
  const [stats,        setStats]        = useState(null)
  const [activeTab,    setActiveTab]    = useState(0)
  const [loading,      setLoading]      = useState(true)
  const [notFound,     setNotFound]     = useState(false)

  useEffect(() => {
    if (!id) return
    setLoading(true)

    Promise.all([
      vendorApi.get(id),
      catalogApi.listExperiences(id, { include_drafts: false }),
      catalogApi.listProducts(id,    { include_drafts: false }),
      reviewApi.vendorReviews(id),
      reviewApi.vendorStats(id),
    ])
      .then(([vRes, eRes, pRes, rRes, sRes]) => {
        setVendor(vRes.data)
        setExperiences(eRes.data || [])
        setProducts(pRes.data    || [])
        setReviews(rRes.data     || [])
        setStats(sRes.data)
      })
      .catch(err => {
        if (err.response?.status === 404) setNotFound(true)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading)  return <><Navbar /><Spinner center size="lg" /></>
  if (notFound) return <NotFound />

  const meta = TYPE_META[vendor.type] || { label: vendor.type, color: '#3b2a1a', bg: '#f5f0e8' }

  return (
    <div className="vdetail">
      <Navbar />

      {/* ── Hero ──────────────────────────────────────────────────── */}
      <div className="vdetail__hero">
        <div
          className="vdetail__hero-bg"
          style={{ background: `linear-gradient(135deg, ${meta.bg} 0%, ${meta.bg}88 100%)` }}
        >
          <div className="vdetail__hero-pattern" aria-hidden />
        </div>

        <div className="vdetail__hero-inner">
          {/* Left — identity */}
          <div className="vdetail__identity">
            <div className="vdetail__avatar" style={{ background: meta.bg, color: meta.color }}>
              {vendor.name.charAt(0)}
            </div>
            <div className="vdetail__identity-info">
              <div className="vdetail__badges">
                <span className="vdetail__type-badge" style={{ background: meta.bg, color: meta.color }}>
                  {meta.label}
                </span>
                {vendor.tier === 'PRO' && (
                  <span className="vdetail__pro-badge">PRO</span>
                )}
              </div>
              <h1 className="vdetail__name">{vendor.name}</h1>
              {vendor.region && (
                <p className="vdetail__location">
                  <span className="vdetail__location-dot" />
                  {vendor.address || vendor.region}
                </p>
              )}
            </div>
          </div>

          {/* Right — stats */}
          <div className="vdetail__hero-stats">
            {stats && stats.total_reviews > 0 && (
              <div className="vdetail__hero-stat">
                <span className="vdetail__hero-stat-value">
                  {stats.average_rating.toFixed(1)}
                </span>
                <span className="vdetail__hero-stat-label">
                  <Stars rating={stats.average_rating} />
                  {stats.total_reviews} komente
                </span>
              </div>
            )}
            <div className="vdetail__hero-stat">
              <span className="vdetail__hero-stat-value">{experiences.length}</span>
              <span className="vdetail__hero-stat-label">Eksperienca</span>
            </div>
            <div className="vdetail__hero-stat">
              <span className="vdetail__hero-stat-value">{products.length}</span>
              <span className="vdetail__hero-stat-label">Produkte</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Body ──────────────────────────────────────────────────── */}
      <div className="vdetail__body">

        {/* ── Left column ───────────────────────────────────────── */}
        <aside className="vdetail__aside">

          {/* About */}
          {vendor.description && (
            <div className="vdetail__card">
              <p className="vdetail__card-label">Rreth nesh</p>
              <p className="vdetail__about">{vendor.description}</p>
            </div>
          )}

          {/* Contact */}
          <div className="vdetail__card">
            <p className="vdetail__card-label">Kontakt</p>
            <div className="vdetail__contacts">
              {vendor.phone && (
                <a href={`tel:${vendor.phone}`} className="vdetail__contact-row">
                  <span className="vdetail__contact-icon">◎</span>
                  {vendor.phone}
                </a>
              )}
              {vendor.email && (
                <a href={`mailto:${vendor.email}`} className="vdetail__contact-row">
                  <span className="vdetail__contact-icon">◈</span>
                  {vendor.email}
                </a>
              )}
              {vendor.website && (
  <a
    href={vendor.website}
    target="_blank"
    rel="noopener noreferrer"
    className="vdetail__contact-row"
  >
    <span className="vdetail__contact-icon">◇</span>
    {vendor.website.replace(/^https?:\/\//, '')}
  </a>
)}

              {vendor.address && (
                <div className="vdetail__contact-row">
                  <span className="vdetail__contact-icon">◉</span>
                  {vendor.address}
                </div>
              )}
            </div>
          </div>

          {/* Map placeholder */}
          {vendor.lat && vendor.lng && (
            <div className="vdetail__card vdetail__card--map">
              <p className="vdetail__card-label">Vendndodhja</p>
              <div className="vdetail__map-placeholder">
                <div className="vdetail__map-coords">
  <span>{vendor.lat.toFixed(4)}° N</span>
  <span>{vendor.lng.toFixed(4)}° E</span>
</div>
<a
  href={`https://maps.google.com/?q=${vendor.lat},${vendor.lng}`}
  target="_blank"
  rel="noopener noreferrer"
  className="vdetail__map-link"
>
  Hap në Google Maps →
</a>

              </div>
            </div>
          )}
        </aside>

        {/* ── Right column ──────────────────────────────────────── */}
        <main className="vdetail__main">

          {/* Tabs */}
          <div className="vdetail__tabs" role="tablist">
            {TABS.map((tab, i) => (
              <button
                key={tab}
                role="tab"
                aria-selected={activeTab === i}
                className={`vdetail__tab ${activeTab === i ? 'vdetail__tab--active' : ''}`}
                onClick={() => setActiveTab(i)}
              >
                {tab}
                <span className="vdetail__tab-count">
                  {i === 0 ? experiences.length :
                   i === 1 ? products.length :
                   reviews.length}
                </span>
              </button>
            ))}
          </div>

          {/* Tab panels */}
          <div className="vdetail__panel" role="tabpanel">

            {/* Experiences */}
            {activeTab === 0 && (
              experiences.length > 0 ? (
                <div className="vdetail__experiences">
                  {experiences.map(exp => (
                    <ExperienceCard key={exp.id} exp={exp} vendorId={id} user={user} />
                  ))}
                </div>
              ) : (
                <Empty message="Ende pa eksperienca të listuara." />
              )
            )}

            {/* Products */}
            {activeTab === 1 && (
              products.length > 0 ? (
                <div className="vdetail__products">
                  {products.map(p => (
                    <ProductCard key={p.id} product={p} />
                  ))}
                </div>
              ) : (
                <Empty message="Ende pa produkte të listuara." />
              )
            )}

            {/* Reviews */}
            {activeTab === 2 && (
              <div className="vdetail__reviews">
                {stats && stats.total_reviews > 0 && (
                  <RatingBreakdown stats={stats} />
                )}
                {reviews.length > 0 ? (
                  reviews.map(r => (
                    <ReviewCard key={r.id} review={r} />
                  ))
                ) : (
                  <Empty message="Ende pa komente. Bëhu i pari!" />
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

// ── Experience Card ────────────────────────────────────────────────────────────
function ExperienceCard({ exp, vendorId, user }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="exp-card">
      <div className="exp-card__header">
        <div className="exp-card__header-left">
          <span className="exp-card__type">
            {EXP_TYPE_LABELS[exp.type] || exp.type}
          </span>
          <h3 className="exp-card__title">{exp.title}</h3>
          <div className="exp-card__meta">
            {exp.duration_minutes && (
              <span className="exp-card__meta-item">
                ◎ {formatDuration(exp.duration_minutes)}
              </span>
            )}
            <span className="exp-card__meta-item">
              ◈ Deri në {exp.capacity} persona
            </span>
          </div>
        </div>
        <div className="exp-card__header-right">
          <div className="exp-card__price">
            <span className="exp-card__price-value">
              €{Number(exp.base_price).toFixed(2)}
            </span>
            <span className="exp-card__price-label">/ person</span>
          </div>
          <Link
            to={`/experiences/${exp.id}/book`}
            className="exp-card__book-btn"
          >
            Rezervo
          </Link>
        </div>
      </div>

      {exp.description && (
        <>
          <p className={`exp-card__desc ${expanded ? 'exp-card__desc--expanded' : ''}`}>
            {exp.description}
          </p>
          {exp.description.length > 120 && (
            <button
              className="exp-card__toggle"
              onClick={() => setExpanded(e => !e)}
            >
              {expanded ? 'Shfaq më pak ↑' : 'Shfaq më shumë ↓'}
            </button>
          )}
        </>
      )}
    </div>
  )
}

// ── Product Card ───────────────────────────────────────────────────────────────
function ProductCard({ product }) {
  const isOutOfStock = product.status === 'out_of_stock' || product.stock_qty === 0

  return (
    <div className={`prod-card ${isOutOfStock ? 'prod-card--oos' : ''}`}>
      <div className="prod-card__img">
        <span className="prod-card__initial">
          {product.name.charAt(0)}
        </span>
        {isOutOfStock && (
          <div className="prod-card__oos-overlay">
            <span>E shitur</span>
          </div>
        )}
      </div>

      <div className="prod-card__body">
        <div>
          <span className="prod-card__category">
            {CAT_LABELS[product.category] || product.category}
          </span>
          <h3 className="prod-card__name">{product.name}</h3>
          {product.description && (
            <p className="prod-card__desc">
              {product.description.length > 80
                ? product.description.slice(0, 80) + '…'
                : product.description}
            </p>
          )}
        </div>

        <div className="prod-card__footer">
          <div className="prod-card__price-wrap">
            <span className="prod-card__price">
              €{Number(product.price).toFixed(2)}
            </span>
            {product.shippable && (
              <span className="prod-card__ship">◎ Dërgim i disponueshëm</span>
            )}
          </div>
          <button
            className="prod-card__btn"
            disabled={isOutOfStock}
          >
            {isOutOfStock ? 'E shitur' : 'Shto në shportë'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Rating breakdown ───────────────────────────────────────────────────────────
function RatingBreakdown({ stats }) {
  return (
    <div className="rating-breakdown">
      <div className="rating-breakdown__score">
        <span className="rating-breakdown__big">
          {stats.average_rating.toFixed(1)}
        </span>
        <Stars rating={stats.average_rating} size="lg" />
        <span className="rating-breakdown__total">
          {stats.total_reviews} komente
        </span>
      </div>
      <div className="rating-breakdown__bars">
        {[5, 4, 3, 2, 1].map(star => {
          const count = stats.rating_breakdown[star] || 0
          const pct   = stats.total_reviews > 0
            ? Math.round((count / stats.total_reviews) * 100)
            : 0
          return (
            <div key={star} className="rating-breakdown__row">
              <span className="rating-breakdown__star">{star} ★</span>
              <div className="rating-breakdown__bar-wrap">
                <div
                  className="rating-breakdown__bar-fill"
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="rating-breakdown__pct">{pct}%</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Review Card ────────────────────────────────────────────────────────────────
function ReviewCard({ review }) {
  return (
    <div className="review-card">
      <div className="review-card__header">
        <div className="review-card__avatar">
          {(review.reviewer_name || '?').charAt(0).toUpperCase()}
        </div>
        <div className="review-card__meta">
          <span className="review-card__name">
            {review.reviewer_name || 'Vizitor'}
          </span>
          <div className="review-card__stars">
            <Stars rating={review.rating} />
            <span className="review-card__date">
              {formatDate(review.created_at)}
            </span>
          </div>
        </div>
        {review.verified_visit && (
          <span className="review-card__verified">✓ Vizitë e verifikuar</span>
        )}
      </div>

      {review.body && (
        <p className="review-card__body">{review.body}</p>
      )}

      {review.vendor_reply && (
        <div className="review-card__reply">
          <p className="review-card__reply-label">Përgjigja e pronarit</p>
          <p className="review-card__reply-body">{review.vendor_reply}</p>
        </div>
      )}
    </div>
  )
}

// ── Stars ──────────────────────────────────────────────────────────────────────
function Stars({ rating, size = 'sm' }) {
  return (
    <span className={`stars stars--${size}`} aria-label={`${rating} yje`}>
      {[1, 2, 3, 4, 5].map(i => (
        <span
          key={i}
          className={`stars__star ${i <= Math.round(rating) ? 'stars__star--filled' : ''}`}
        >
          ★
        </span>
      ))}
    </span>
  )
}

// ── Empty ──────────────────────────────────────────────────────────────────────
function Empty({ message }) {
  return (
    <div className="vdetail__empty">
      <span className="vdetail__empty-icon">◎</span>
      <p>{message}</p>
    </div>
  )
}

// ── Not found ──────────────────────────────────────────────────────────────────
function NotFound() {
  return (
    <>
      <Navbar />
      <div className="vdetail__notfound">
        <h2>Vendi nuk u gjet</h2>
        <p>Ky vendor nuk ekziston ose nuk është aktiv.</p>
        <Link to="/explore" className="vdetail__notfound-link">
          ← Kthehu te eksplorimi
        </Link>
      </div>
    </>
  )
}

// ── Helpers ────────────────────────────────────────────────────────────────────
function formatDuration(minutes) {
  if (minutes < 60)  return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}h ${m}min` : `${h} orë`
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('sq-AL', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}