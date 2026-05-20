export const tokenStorage = {
  getAccess:  ()       => localStorage.getItem('farmalb_access_token'),
  getRefresh: ()       => localStorage.getItem('farmalb_refresh_token'),
  setTokens:  (a, r)   => {
    localStorage.setItem('farmalb_access_token', a)
    localStorage.setItem('farmalb_refresh_token', r)
  },
  clear: () => {
    localStorage.removeItem('farmalb_access_token')
    localStorage.removeItem('farmalb_refresh_token')
  },
}

export const parseJwt = (token) => {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return null
  }
}

export const isTokenExpired = (token) => {
  const payload = parseJwt(token)
  if (!payload?.exp) return true
  return Date.now() >= payload.exp * 1000
}