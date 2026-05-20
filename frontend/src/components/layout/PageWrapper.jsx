import Navbar from './Navbar'
import './PageWrapper.css'

export default function PageWrapper({ children, fullWidth = false }) {
  return (
    <div className="page">
      <Navbar />
      <main className={`page__main ${fullWidth ? 'page__main--full' : ''}`}>
        {children}
      </main>
      <footer className="page__footer">
        <div className="page__footer-inner">
          <span className="page__footer-brand">FarmaAlb</span>
          <span className="page__footer-copy">© {new Date().getFullYear()} — Shqipëria Rurale</span>
        </div>
      </footer>
    </div>
  )
}