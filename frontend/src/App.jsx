import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import LoginPage   from './pages/LoginPage'
import LandingPage from './pages/LandingPage'
import RegisterPage from './pages/RegisterPage'
import ExplorePage  from './pages/ExplorePage'
import VendorDetailPage from './pages/VendorDetailPage'
import DashboardPage from './pages/DashboardPage'

import Spinner     from './components/ui/Spinner'
import './styles/globals.css'

function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <Spinner center size="lg" />
  if (!user)   return <Navigate to="/login" replace />
  return children
}

const Placeholder = ({ name }) => (
  <div style={{ padding: '64px 32px', textAlign: 'center', fontFamily: 'var(--font-display)', fontSize: 32 }}>
    {name}
  </div>
)

function AppRoutes() {
  const { user, loading } = useAuth()
  if (loading) return <Spinner center size="lg" />

  return (
    <Routes>
      <Route path="/"          element={<LandingPage />} />
      <Route path="/explore"   element={<ExplorePage />} />
      <Route path="/login"     element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />}/>
      <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
      <Route path="/vendors/:id" element={<VendorDetailPage />} />
      <Route path="*"          element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}