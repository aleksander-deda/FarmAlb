import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import './Navbar.css'

const NAV_LINKS = [
  { to: '/explore',   label: 'Eksplorо' },
  { to: '/experiences', label: 'Eksperienca' },
  { to: '/products',  label: 'Produkte' },
  { to: '/about',     label: 'Rreth nesh' },
]

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="navbar">
      <div className="navbar__inner">
        {/* Brand */}
        <Link to="/" className="navbar__brand">
          <span className="navbar__brand-icon">⊕</span>
          <span className="navbar__brand-name">FarmaAlb</span>
        </Link>

        {/* Desktop nav */}
        <nav className="navbar__links" aria-label="Navigimi kryesor">
          {NAV_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`navbar__link ${location.pathname === to ? 'navbar__link--active' : ''}`}
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Actions */}
        <div className="navbar__actions">
          {user ? (
            <div className="navbar__user">
              <Link to="/dashboard" className="navbar__user-name">
                {user.full_name.split(' ')[0]}
              </Link>
              <button className="navbar__logout" onClick={handleLogout}>
                Dil
              </button>
            </div>
          ) : (
            <>
              <Link to="/login"    className="navbar__action-link">Hyr</Link>
              <Link to="/register" className="navbar__action-btn">Regjistrohu</Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="navbar__hamburger"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Menu"
          aria-expanded={menuOpen}
        >
          <span /><span /><span />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="navbar__mobile">
          {NAV_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className="navbar__mobile-link"
              onClick={() => setMenuOpen(false)}
            >
              {label}
            </Link>
          ))}
          <div className="navbar__mobile-divider" />
          {user ? (
            <button className="navbar__mobile-link" onClick={handleLogout}>Dil</button>
          ) : (
            <>
              <Link to="/login"    className="navbar__mobile-link" onClick={() => setMenuOpen(false)}>Hyr</Link>
              <Link to="/register" className="navbar__mobile-link" onClick={() => setMenuOpen(false)}>Regjistrohu</Link>
            </>
          )}
        </div>
      )}
    </header>
  )
}