import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/layout/Navbar'
import Spinner from '../components/ui/Spinner'
import {
  bookingApi, orderApi, vendorApi,
  catalogApi, reviewApi, adminApi,
} from '../lib/api'
import './DashboardPage.css'

const STATUS_COLORS = {
  pending:    { bg: '#faeeda', color: '#854f0b' },
  confirmed:  { bg: '#e1f5ee', color: '#085041' },
  cancelled:  { bg: '#faece7', color: '#712b13' },
  completed:  { bg: '#eef2ea', color: '#27500a' },
  shipped:    { bg: '#e6f1fb', color: '#0c447c' },
  delivered:  { bg: '#eef2ea', color: '#27500a' },
  active:     { bg: '#e1f5ee', color: '#085041' },
  draft:      { bg: '#f1efe8', color: '#5f5e5a' },
  archived:   { bg: '#f1efe8', color: '#5f5e5a' },
  published:  { bg: '#e1f5ee', color: '#085041' },
  rejected:   { bg: '#faece7', color: '#712b13' },
  approved:   { bg: '#e1f5ee', color: '#085041' },
  open:       { bg: '#e1f5ee', color: '#085041' },
  full:       { bg: '#faeeda', color: '#854f0b' },
}

function StatusBadge({ status }) {
  const s = STATUS_COLORS[status] || { bg: '#f1efe8', color: '#5f5e5a' }
  return (
    <span className="status-badge" style={{ background: s.bg, color: s.color }}>
      {status}
    </span>
  )
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="stat-card" style={accent ? { borderTop: `3px solid ${accent}` } : {}}>
      <p className="stat-card__label">{label}</p>
      <p className="stat-card__value">{value ?? '—'}</p>
      {sub && <p className="stat-card__sub">{sub}</p>}
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  if (!user) return null

  return (
    <div className="dash">
      <Navbar />
      <div className="dash__body">
        <aside className="dash__sidebar">
          <div className="dash__sidebar-user">
            <div className="dash__avatar">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="dash__sidebar-name">{user.full_name}</p>
              <p className="dash__sidebar-email">{user.email}</p>
            </div>
          </div>
          <div className="dash__sidebar-role">
            <span className="dash__role-badge">
              {user.is_superuser ? 'Super Admin' : 'Përdorues'}
            </span>
          </div>
        </aside>

        <main className="dash__main">
          {user.is_superuser
            ? <AdminDashboard />
            : <GuestDashboard user={user} />
          }
        </main>
      </div>
    </div>
  )
}

// ── Guest Dashboard ────────────────────────────────────────────────────────────
function GuestDashboard({ user }) {
  const [bookings, setBookings] = useState([])
  const [orders,   setOrders]   = useState([])
  const [loading,  setLoading]  = useState(true)
  const [tab,      setTab]      = useState(0)

  useEffect(() => {
    Promise.all([
      bookingApi.myBookings(),
      orderApi.myOrders(),
    ])
      .then(([b, o]) => {
        setBookings(b.data || [])
        setOrders(o.data   || [])
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner center />

  const pendingBookings   = bookings.filter(b => b.status === 'pending').length
  const confirmedBookings = bookings.filter(b => b.status === 'confirmed').length
  const totalSpent = orders
    .filter(o => o.status !== 'cancelled')
    .reduce((s, o) => s + Number(o.total), 0)

  return (
    <div className="dash__section">
      <div className="dash__header">
        <h1 className="dash__title">Mirë se erdhe, {user.full_name.split(' ')[0]}</h1>
        <p className="dash__subtitle">Menaxho rezervimet dhe porositë tuaja</p>
      </div>

      {/* Stats */}
      <div className="dash__stats">
        <StatCard
          label="Rezervime totale"
          value={bookings.length}
          sub={`${confirmedBookings} të konfirmuara`}
          accent="var(--color-terracotta)"
        />
        <StatCard
          label="Porosi totale"
          value={orders.length}
          sub={`${orders.filter(o => o.status === 'delivered').length} të dërguara`}
          accent="var(--color-olive)"
        />
        <StatCard
          label="Shpenzuar gjithsej"
          value={`€${totalSpent.toFixed(2)}`}
          sub="Produkte & eksperienca"
          accent="#c4a44a"
        />
        <StatCard
          label="Në pritje"
          value={pendingBookings + orders.filter(o => o.status === 'pending').length}
          sub="Rezervime & porosi"
          accent="#378add"
        />
      </div>

      {/* Tabs */}
      <div className="dash__tabs">
        {['Rezervimet', 'Porositë'].map((t, i) => (
          <button
            key={t}
            className={`dash__tab ${tab === i ? 'dash__tab--active' : ''}`}
            onClick={() => setTab(i)}
          >
            {t}
            <span className="dash__tab-count">
              {i === 0 ? bookings.length : orders.length}
            </span>
          </button>
        ))}
      </div>

      {tab === 0 && (
        bookings.length > 0 ? (
          <div className="dash__table-wrap">
            <table className="dash__table">
              <thead>
                <tr>
                  <th>Eksperienca</th>
                  <th>Mysafirë</th>
                  <th>Totali</th>
                  <th>Statusi</th>
                  <th>Pagesa</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {bookings.map(b => (
                  <tr key={b.id}>
                    <td>
                      <div className="dash__cell-title">
                        {b.experience_title || 'Eksperiencë'}
                      </div>
                      <div className="dash__cell-sub">
                        {b.slot_starts_at
                          ? new Date(b.slot_starts_at).toLocaleDateString('sq-AL',
                              { day: 'numeric', month: 'short', year: 'numeric' })
                          : '—'}
                      </div>
                    </td>
                    <td>{b.guests}</td>
                    <td>€{Number(b.total).toFixed(2)}</td>
                    <td><StatusBadge status={b.status} /></td>
                    <td><StatusBadge status={b.payment_status || 'pending'} /></td>
                    <td>
                      {b.status === 'pending' || b.status === 'confirmed' ? (
                        <CancelBookingBtn id={b.id} onDone={() =>
                          setBookings(prev => prev.map(x =>
                            x.id === b.id ? { ...x, status: 'cancelled' } : x
                          ))
                        } />
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            message="Nuk keni rezervime ende."
            cta="Eksploroni eksperiencat"
            to="/explore"
          />
        )
      )}

      {tab === 1 && (
        orders.length > 0 ? (
          <div className="dash__table-wrap">
            <table className="dash__table">
              <thead>
                <tr>
                  <th>Porosia</th>
                  <th>Artikuj</th>
                  <th>Totali</th>
                  <th>Statusi</th>
                  <th>Gjurmim</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {orders.map(o => (
                  <tr key={o.id}>
                    <td>
                      <div className="dash__cell-title">
                        #{o.id.slice(0, 8).toUpperCase()}
                      </div>
                      <div className="dash__cell-sub">
                        {new Date(o.placed_at || o.created_at).toLocaleDateString('sq-AL',
                          { day: 'numeric', month: 'short', year: 'numeric' })}
                      </div>
                    </td>
                    <td>{o.items?.length ?? '—'}</td>
                    <td>€{Number(o.total).toFixed(2)}</td>
                    <td><StatusBadge status={o.status} /></td>
                    <td>
                      {o.tracking_number
                        ? <span className="dash__tracking">{o.tracking_number}</span>
                        : <span className="dash__cell-sub">—</span>}
                    </td>
                    <td>
                      {(o.status === 'pending' || o.status === 'confirmed') && (
                        <CancelOrderBtn id={o.id} onDone={() =>
                          setOrders(prev => prev.map(x =>
                            x.id === o.id ? { ...x, status: 'cancelled' } : x
                          ))
                        } />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            message="Nuk keni porosi ende."
            cta="Shikoni produktet"
            to="/explore"
          />
        )
      )}
    </div>
  )
}

// ── Admin Dashboard ────────────────────────────────────────────────────────────
function AdminDashboard() {
  const [vendors,      setVendors]      = useState([])
  const [applications, setApplications] = useState([])
  const [auditLogs,    setAuditLogs]    = useState([])
  const [loading,      setLoading]      = useState(true)
  const [tab,          setTab]          = useState(0)

  const loadData = () => {
    setLoading(true)
    Promise.all([
      vendorApi.list(),
      vendorApi.listApplications(),
      adminApi.auditLogs({ limit: 30 }),
    ])
      .then(([v, a, l]) => {
        setVendors(v.data      || [])
        setApplications(a.data || [])
        setAuditLogs(l.data?.results || [])
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadData() }, [])

  if (loading) return <Spinner center />

  const pendingApps = applications.filter(a => a.status === 'pending').length
  const activeVendors = vendors.filter(v => v.status === 'active').length
  const proVendors = vendors.filter(v => v.tier === 'PRO').length

  return (
    <div className="dash__section">
      <div className="dash__header">
        <h1 className="dash__title">Paneli i Administrimit</h1>
        <p className="dash__subtitle">Menaxho platformën FarmaAlb</p>
      </div>

      {/* Stats */}
      <div className="dash__stats">
        <StatCard
          label="Vendorë aktivë"
          value={activeVendors}
          sub={`${proVendors} PRO`}
          accent="var(--color-terracotta)"
        />
        <StatCard
          label="Aplikime në pritje"
          value={pendingApps}
          sub="Kërkojnë rishikim"
          accent={pendingApps > 0 ? '#d4861a' : 'var(--color-olive)'}
        />
        <StatCard
          label="Vendorë gjithsej"
          value={vendors.length}
          sub="Të regjistruar"
          accent="var(--color-olive)"
        />
        <StatCard
          label="Veprime të fundit"
          value={auditLogs.length}
          sub="Log i auditimit"
          accent="#378add"
        />
      </div>

      {/* Tabs */}
      <div className="dash__tabs">
        {['Vendorët', 'Aplikime', 'Log Auditimi'].map((t, i) => (
          <button
            key={t}
            className={`dash__tab ${tab === i ? 'dash__tab--active' : ''}`}
            onClick={() => setTab(i)}
          >
            {t}
            {i === 1 && pendingApps > 0 && (
              <span className="dash__tab-alert">{pendingApps}</span>
            )}
          </button>
        ))}
      </div>

      {/* Vendors tab */}
      {tab === 0 && (
        vendors.length > 0 ? (
          <div className="dash__table-wrap">
            <table className="dash__table">
              <thead>
                <tr>
                  <th>Emri</th>
                  <th>Tipi</th>
                  <th>Rajoni</th>
                  <th>Statusi</th>
                  <th>Tier</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {vendors.map(v => (
                  <tr key={v.id}>
                    <td>
                      <div className="dash__cell-title">{v.name}</div>
                      {v.email && (
                        <div className="dash__cell-sub">{v.email}</div>
                      )}
                    </td>
                    <td>
                      <span className="dash__type-pill">{v.type}</span>
                    </td>
                    <td>{v.region || '—'}</td>
                    <td><StatusBadge status={v.status} /></td>
                    <td>
                      <span className={`dash__tier ${v.tier === 'PRO' ? 'dash__tier--pro' : ''}`}>
                        {v.tier}
                      </span>
                    </td>
                    <td>
                      <Link to={`/vendors/${v.id}`} className="dash__action-link">
                        Shiko →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="Ende pa vendorë të regjistruar." />
        )
      )}

      {/* Applications tab */}
      {tab === 1 && (
        applications.length > 0 ? (
          <div className="dash__table-wrap">
            <table className="dash__table">
              <thead>
                <tr>
                  <th>Biznesi</th>
                  <th>Tipi</th>
                  <th>Rajoni</th>
                  <th>Statusi</th>
                  <th>Aplikuar</th>
                  <th>Veprime</th>
                </tr>
              </thead>
              <tbody>
                {applications.map(a => (
                  <tr key={a.id}>
                    <td>
                      <div className="dash__cell-title">{a.business_name}</div>
                      <div className="dash__cell-sub">{a.contact_email}</div>
                    </td>
                    <td>
                      <span className="dash__type-pill">{a.type}</span>
                    </td>
                    <td>{a.region || '—'}</td>
                    <td><StatusBadge status={a.status} /></td>
                    <td>
                      {a.submitted_at
                        ? new Date(a.submitted_at).toLocaleDateString('sq-AL',
                            { day: 'numeric', month: 'short' })
                        : '—'}
                    </td>
                    <td>
                      {a.status === 'pending' && (
                        <div className="dash__action-btns">
                          <ApproveBtn id={a.id} onDone={loadData} />
                          <RejectBtn  id={a.id} onDone={loadData} />
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="Nuk ka aplikime." />
        )
      )}

      {/* Audit log tab */}
      {tab === 2 && (
        auditLogs.length > 0 ? (
          <div className="dash__table-wrap">
            <table className="dash__table">
              <thead>
                <tr>
                  <th>Veprimi</th>
                  <th>Resursi</th>
                  <th>Aktori</th>
                  <th>IP</th>
                  <th>Koha</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map(log => (
                  <tr key={log.id}>
                    <td>
                      <span className="dash__audit-action">{log.action}</span>
                    </td>
                    <td>
                      <div className="dash__cell-title">{log.resource_type}</div>
                      {log.resource_id && (
                        <div className="dash__cell-sub">
                          #{log.resource_id.slice(0, 8).toUpperCase()}
                        </div>
                      )}
                    </td>
                    <td>
                      {log.actor_id
                        ? <span className="dash__cell-sub">#{log.actor_id.slice(0, 8).toUpperCase()}</span>
                        : <span className="dash__cell-sub">system</span>}
                    </td>
                    <td>
                      <span className="dash__cell-sub">{log.ip_address || '—'}</span>
                    </td>
                    <td>
                      <span className="dash__cell-sub">
                        {new Date(log.created_at).toLocaleString('sq-AL', {
                          day: 'numeric', month: 'short',
                          hour: '2-digit', minute: '2-digit',
                        })}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="Ende pa log auditimi." />
        )
      )}
    </div>
  )
}

// ── Action buttons ─────────────────────────────────────────────────────────────
function CancelBookingBtn({ id, onDone }) {
  const [loading, setLoading] = useState(false)
  const handle = async () => {
    if (!confirm('Jeni të sigurt që doni të anuloni këtë rezervim?')) return
    setLoading(true)
    try { await bookingApi.cancel(id, { reason: 'Anuluar nga klienti' }); onDone() }
    catch { alert('Gabim gjatë anulimit.') }
    finally { setLoading(false) }
  }
  return (
    <button className="dash__btn dash__btn--danger" onClick={handle} disabled={loading}>
      {loading ? '…' : 'Anulo'}
    </button>
  )
}

function CancelOrderBtn({ id, onDone }) {
  const [loading, setLoading] = useState(false)
  const handle = async () => {
    if (!confirm('Jeni të sigurt që doni të anuloni këtë porosi?')) return
    setLoading(true)
    try { await orderApi.cancel(id, { reason: 'Anuluar nga klienti' }); onDone() }
    catch { alert('Gabim gjatë anulimit.') }
    finally { setLoading(false) }
  }
  return (
    <button className="dash__btn dash__btn--danger" onClick={handle} disabled={loading}>
      {loading ? '…' : 'Anulo'}
    </button>
  )
}

function ApproveBtn({ id, onDone }) {
  const [loading, setLoading] = useState(false)
  const handle = async () => {
    setLoading(true)
    try { await vendorApi.approve(id); onDone() }
    catch { alert('Gabim gjatë aprovimit.') }
    finally { setLoading(false) }
  }
  return (
    <button className="dash__btn dash__btn--success" onClick={handle} disabled={loading}>
      {loading ? '…' : 'Aprovo'}
    </button>
  )
}

function RejectBtn({ id, onDone }) {
  const [loading, setLoading] = useState(false)
  const handle = async () => {
    const reason = prompt('Arsyeja e refuzimit (opsionale):')
    if (reason === null) return
    setLoading(true)
    try { await vendorApi.reject(id, reason); onDone() }
    catch { alert('Gabim gjatë refuzimit.') }
    finally { setLoading(false) }
  }
  return (
    <button className="dash__btn dash__btn--danger" onClick={handle} disabled={loading}>
      {loading ? '…' : 'Refuzo'}
    </button>
  )
}

// ── Empty state ────────────────────────────────────────────────────────────────
function EmptyState({ message, cta, to }) {
  return (
    <div className="dash__empty">
      <span className="dash__empty-icon">◎</span>
      <p>{message}</p>
      {cta && to && (
        <Link to={to} className="dash__empty-btn">{cta} →</Link>
      )}
    </div>
  )
}