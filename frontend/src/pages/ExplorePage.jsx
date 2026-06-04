import { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { vendorApi } from '../lib/api'
import Navbar from '../components/layout/Navbar'
import './ExplorePage.css'

const TYPES = [
  { code: '',            label: 'Të gjitha' },
  { code: 'FARM',        label: 'Ferma',       emoji: '🌾' },
  { code: 'WINERY',      label: 'Vreshtari',   emoji: '🍇' },
  { code: 'AGRITOURISM', label: 'Agriturizma', emoji: '🏡' },
  { code: 'RESTAURANT',  label: 'Restorante',  emoji: '🍽️' },
]

const REGIONS = [
  '', 'Tirana', 'Shkodra', 'Vlora', 'Korça',
  'Berati', 'Gjirokastra', 'Elbasani', 'Lezha', 'Dibra',
]

const SORT_OPTIONS = [
  { value: 'newest',   label: 'Më të rejat' },
  { value: 'name_asc', label: 'Emri (A–Z)' },
  { value: 'name_desc', label: 'Emri (Z–A)' },
]

const TYPE_META = {
  FARM:        { label: 'Fermë',       color: '#4a5240', bg: '#eef2ea' },
  WINERY:      { label: 'Vreshtari',   color: '#6b3a2a', bg: '#f5ece8' },
  AGRITOURISM: { label: 'Agriturizma', color: '#2a4a5a', bg: '#e8f2f5' },
  RESTAURANT:  { label: 'Restorant',   color: '#3a3a2a', bg: '#f2f2e8' },
}

export default function ExplorePage() {
  const [searchParams, setSearchParams] = useSearchParams()

  const [vendors,   setVendors]   = useState([])
  const [loading,   setLoading]   = useState(true)
  const [total,     setTotal]     = useState(0)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const type   = searchParams.get('type')   || ''
  const region = searchParams.get('region') || ''
  const sort   = searchParams.get('sort')   || 'newest'
  const search = searchParams.get('q')      || ''

  const setParam = (key, val) => {
    const next = new URLSearchParams(searchParams)
    if (val) next.set(key, val)
    else next.delete(key)
    setSearchParams(next)
  }

  const clearAll = () => setSearchParams({})

  const hasFilters = type || region || search

  const fetchVendors = useCallback(() => {
    setLoading(true)
    vendorApi.list({ type: type || undefined, region: region || undefined })
      .then(vendors => {
        let data = vendors || []
        if (search) {
          const q = search.toLowerCase()
          data = data.filter(v =>
            v.name.toLowerCase().includes(q) ||
            v.description?.toLowerCase().includes(q) ||
            v.region?.toLowerCase().includes(q)
          )
        }
        if (sort === 'name_asc')  data = [...data].sort((a, b) => a.name.localeCompare(b.name))
        if (sort === 'name_desc') data = [...data].sort((a, b) => b.name.localeCompare(a.name))
        setTotal(data.length)
        setVendors(data)
      })
      .catch(() => setVendors([]))
      .finally(() => setLoading(false))
  }, [type, region, sort, search])

  useEffect(() => { fetchVendors() }, [fetchVendors])

  return (
    <div className="explore">
      <Navbar />

      {/* ── Top bar ───────────────────────────────────────────────── */}
      <div className="explore__topbar">
        <div className="explore__topbar-inner">
          {/* Search */}
          <div className="explore__search-wrap">
            <span className="explore__search-icon">⊕</span>
            <input
              className="explore__search"
              type="search"
              placeholder="Kërko ferma, vreshtari, rajone..."
              value={search}
              onChange={e => setParam('q', e.target.value)}
              aria-label="Kërko"
            />
            {search && (
              <button
                className="explore__search-clear"
                onClick={() => setParam('q', '')}
                aria-label="Pastro"
              >✕</button>
            )}
          </div>

          {/* Sort */}
          <select
            className="explore__sort"
            value={sort}
            onChange={e => setParam('sort', e.target.value)}
            aria-label="Rendit"
          >
            {SORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>

          {/* Mobile filter toggle */}
          <button
            className="explore__filter-toggle"
            onClick={() => setSidebarOpen(o => !o)}
            aria-expanded={sidebarOpen}
            aria-label="Filtrat"
          >
            <span className="explore__filter-toggle-icon">⊞</span>
            Filtrat
            {hasFilters && <span className="explore__filter-badge" />}
          </button>
        </div>
      </div>

      <div className="explore__body">

        {/* ── Sidebar ───────────────────────────────────────────────── */}
        <aside className={`explore__sidebar ${sidebarOpen ? 'explore__sidebar--open' : ''}`}>
          <div className="explore__sidebar-header">
            <span className="explore__sidebar-title">Filtrat</span>
            {hasFilters && (
              <button className="explore__clear" onClick={clearAll}>
                Pastro të gjitha
              </button>
            )}
          </div>

          {/* Type filter */}
          <div className="filter-group">
            <p className="filter-group__label">Kategoria</p>
            <div className="filter-group__pills">
              {TYPES.map(t => (
                <button
                  key={t.code}
                  className={`filter-pill ${type === t.code ? 'filter-pill--active' : ''}`}
                  onClick={() => setParam('type', t.code)}
                >
                  {t.emoji && <span>{t.emoji}</span>}
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Region filter */}
          <div className="filter-group">
            <p className="filter-group__label">Rajoni</p>
            <div className="filter-group__list">
              {REGIONS.map(r => (
                <button
                  key={r}
                  className={`filter-region ${region === r ? 'filter-region--active' : ''}`}
                  onClick={() => setParam('region', r)}
                >
                  {r || 'Të gjitha rajonet'}
                  {region === r && <span className="filter-region__check">✓</span>}
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* ── Main content ──────────────────────────────────────────── */}
        <main className="explore__main">

          {/* Results header */}
          <div className="explore__results-header">
            {!loading && (
              <p className="explore__count">
                <strong>{total}</strong> {total === 1 ? 'vend' : 'vende'}
                {type && ` · ${TYPES.find(t => t.code === type)?.label}`}
                {region && ` · ${region}`}
                {search && ` · "${search}"`}
              </p>
            )}

            {/* Active filter chips */}
            {hasFilters && (
              <div className="explore__chips">
                {type && (
                  <span className="explore__chip">
                    {TYPES.find(t => t.code === type)?.label}
                    <button onClick={() => setParam('type', '')} aria-label="Hiq filtrin">✕</button>
                  </span>
                )}
                {region && (
                  <span className="explore__chip">
                    {region}
                    <button onClick={() => setParam('region', '')} aria-label="Hiq filtrin">✕</button>
                  </span>
                )}
                {search && (
                  <span className="explore__chip">
                    "{search}"
                    <button onClick={() => setParam('q', '')} aria-label="Hiq filtrin">✕</button>
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Grid */}
          {loading ? (
            <div className="explore__grid">
              {[...Array(6)].map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : vendors.length > 0 ? (
            <div className="explore__grid">
              {vendors.map((v, i) => (
                <VendorCard key={v.id} vendor={v} index={i} />
              ))}
            </div>
          ) : (
            <EmptyState onClear={clearAll} hasFilters={hasFilters} />
          )}
        </main>
      </div>
    </div>
  )
}

// ── Vendor Card ────────────────────────────────────────────────────────────────
function VendorCard({ vendor, index }) {
  const meta = TYPE_META[vendor.type] || { label: vendor.type, color: '#3b2a1a', bg: '#f5f0e8' }

  return (
    <Link
      to={`/vendors/${vendor.id}`}
      className="vcard"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Image area */}
      <div className="vcard__img">
        <div
          className="vcard__img-placeholder"
          style={{ background: `linear-gradient(135deg, ${meta.bg} 0%, ${meta.bg}cc 100%)` }}
        >
          <span className="vcard__initial" style={{ color: meta.color }}>
            {vendor.name.charAt(0)}
          </span>
          <div className="vcard__img-pattern" aria-hidden />
        </div>

        <span
          className="vcard__badge"
          style={{ background: meta.bg, color: meta.color }}
        >
          {meta.label}
        </span>

        {vendor.tier === 'PRO' && (
          <span className="vcard__pro">PRO</span>
        )}
      </div>

      {/* Body */}
      <div className="vcard__body">
        <div className="vcard__top">
          <h3 className="vcard__name">{vendor.name}</h3>
          {vendor.region && (
            <p className="vcard__region">
              <span className="vcard__region-dot" />
              {vendor.region}
            </p>
          )}
        </div>

        {vendor.description && (
          <p className="vcard__desc">
            {vendor.description.length > 100
              ? vendor.description.slice(0, 100) + '…'
              : vendor.description}
          </p>
        )}

        <div className="vcard__footer">
          <span className="vcard__link">Shiko detajet</span>
          <span className="vcard__arrow">→</span>
        </div>
      </div>
    </Link>
  )
}

// ── Skeleton ───────────────────────────────────────────────────────────────────
function SkeletonCard() {
  return (
    <div className="vcard vcard--skeleton" aria-hidden>
      <div className="vcard__img vcard__skeleton-img" />
      <div className="vcard__body">
        <div className="skeleton-line skeleton-line--title" />
        <div className="skeleton-line skeleton-line--sub" />
        <div className="skeleton-line skeleton-line--desc" />
        <div className="skeleton-line skeleton-line--desc skeleton-line--short" />
      </div>
    </div>
  )
}

// ── Empty state ────────────────────────────────────────────────────────────────
function EmptyState({ onClear, hasFilters }) {
  return (
    <div className="explore__empty">
      <div className="explore__empty-icon">◎</div>
      <h3 className="explore__empty-title">
        {hasFilters ? 'Nuk u gjet asgjë' : 'Ende pa ferma'}
      </h3>
      <p className="explore__empty-desc">
        {hasFilters
          ? 'Provo të ndryshosh filtrat ose të kërkosh me fjalë të tjera.'
          : 'Bëhu ferma e parë në platformë dhe hap dyert për vizitorë.'}
      </p>
      {hasFilters ? (
        <button className="explore__empty-btn" onClick={onClear}>
          Pastro filtrat
        </button>
      ) : (
        <Link to="/register" className="explore__empty-btn">
          Regjistro fermën tënde
        </Link>
      )}
    </div>
  )
}