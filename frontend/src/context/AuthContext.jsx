import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi } from '../lib/api'
import { tokenStorage, isTokenExpired } from '../lib/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)  // true on first mount

  const fetchMe = useCallback(async () => {
    try {
      const user = await authApi.me()
      setUser(user)
    } catch {
      setUser(null)
      tokenStorage.clear()
    }
  }, [])

  // On mount — if we have a valid token, fetch current user
  useEffect(() => {
    const token = tokenStorage.getAccess()
    if (token && !isTokenExpired(token)) {
      fetchMe().finally(() => setLoading(false))
    } else {
      tokenStorage.clear()
      setLoading(false)
    }
  }, [fetchMe])

  const login = async (email, password) => {
    const res = await authApi.login({ email, password })
    const { access_token, refresh_token } = res
    tokenStorage.setTokens(access_token, refresh_token)
    await fetchMe()
  }

  const register = async (data) => {
    const res = await authApi.register(data)
    return res
  }

  const logout = () => {
    tokenStorage.clear()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}