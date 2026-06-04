import axios from 'axios'
import { tokenStorage } from './auth'   // ← import tokenStorage

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle ApiResponse structure: extract data on 2xx, handle errors on 4xx/5xx
api.interceptors.response.use(
  (res) => {
    // Response successful (2xx)
    // Backend returns ApiResponse structure: { success: true, data, message, meta }
    // Extract just the data for convenience
    if (res.data?.success === false) {
      // Response marked as unsuccessful (shouldn't normally happen on 2xx, but handle it)
      const error = new Error(res.data?.message || 'Request failed')
      error.response = res
      error.data = res.data
      throw error
    }
    return res.data?.data !== undefined ? res.data.data : res.data
  },
  (err) => {
    // Response error (4xx/5xx)
    if (err.response?.status === 401) {
      tokenStorage.clear()
      window.location.href = '/login'
    }
    
    // Extract error message from ApiResponse structure
    const errData = err.response?.data
    if (errData?.message) {
      const error = new Error(errData.message)
      error.response = err.response
      error.data = errData
      return Promise.reject(error)
    }
    
    return Promise.reject(err)
  }
)

// ── Auth ───────────────────────────────────────────────────────────────────────
export const authApi = {
  login:    (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  me:       ()     => api.get('/auth/me'),
  refresh:  (data) => api.post('/auth/refresh', data),
}

// ── Vendors ────────────────────────────────────────────────────────────────────
export const vendorApi = {
  list:           (params) => api.get('/vendors', { params }),
  get:            (id)     => api.get(`/vendors/${id}`),
  apply:          (data)   => api.post('/vendors/apply', data),
  myApplication:  ()       => api.get('/vendors/my/application'),
  update:         (id, data) => api.patch(`/vendors/${id}`, data),
  // Admin
  listApplications: (params) => api.get('/vendors/admin/applications', { params }),
  approve:          (id)     => api.post(`/vendors/admin/applications/${id}/approve`),
  reject:           (id, reason) => api.post(`/vendors/admin/applications/${id}/reject`, null, { params: { reason } }),
}

// ── Catalog ────────────────────────────────────────────────────────────────────
export const catalogApi = {
  listExperiences: (vendorId, params) => api.get(`/vendors/${vendorId}/experiences`, { params }),
  getExperience:   (id)               => api.get(`/experiences/${id}`),
  createExperience:(vendorId, data)   => api.post(`/vendors/${vendorId}/experiences`, data),
  updateExperience:(id, data)         => api.patch(`/experiences/${id}`, data),
  deleteExperience:(id)               => api.delete(`/experiences/${id}`),
  listSlots:       (expId, params)    => api.get(`/experiences/${expId}/slots`, { params }),
  createSlot:      (expId, data)      => api.post(`/experiences/${expId}/slots`, data),
  updateSlot:      (id, data)         => api.patch(`/slots/${id}`, data),
  deleteSlot:      (id)               => api.delete(`/slots/${id}`),
  listProducts:    (vendorId, params) => api.get(`/vendors/${vendorId}/products`, { params }),
  getProduct:      (id)               => api.get(`/products/${id}`),
  createProduct:   (vendorId, data)   => api.post(`/vendors/${vendorId}/products`, data),
  updateProduct:   (id, data)         => api.patch(`/products/${id}`, data),
  deleteProduct:   (id)               => api.delete(`/products/${id}`),
}

// ── Bookings ───────────────────────────────────────────────────────────────────
export const bookingApi = {
  create:       (data) => api.post('/bookings', data),
  myBookings:   (params) => api.get('/bookings/me', { params }),
  get:          (id)   => api.get(`/bookings/${id}`),
  cancel:       (id, data) => api.post(`/bookings/${id}/cancel`, data),
  confirm:      (id)   => api.post(`/bookings/${id}/confirm`),
  vendorBookings:(vendorId, params) => api.get(`/bookings/vendor/${vendorId}`, { params }),
}

// ── Orders ─────────────────────────────────────────────────────────────────────
export const orderApi = {
  create:       (data) => api.post('/orders', data),
  myOrders:     (params) => api.get('/orders/me', { params }),
  get:          (id)   => api.get(`/orders/${id}`),
  cancel:       (id, data) => api.post(`/orders/${id}/cancel`, data),
  confirm:      (id)   => api.post(`/orders/${id}/confirm`),
  ship:         (id, data) => api.post(`/orders/${id}/ship`, data),
  deliver:      (id)   => api.post(`/orders/${id}/deliver`),
  vendorOrders: (vendorId, params) => api.get(`/orders/vendor/${vendorId}`, { params }),
}

// ── Promotions ─────────────────────────────────────────────────────────────────
export const promotionApi = {
  list:     (vendorId, params) => api.get(`/promotions/vendors/${vendorId}`, { params }),
  create:   (vendorId, data)   => api.post(`/promotions/vendors/${vendorId}`, data),
  get:      (id)               => api.get(`/promotions/${id}`),
  update:   (id, data)         => api.patch(`/promotions/${id}`, data),
  disable:  (id)               => api.post(`/promotions/${id}/disable`),
  validate: (data)             => api.post('/promotions/validate', data),
}

// ── Reviews ────────────────────────────────────────────────────────────────────
export const reviewApi = {
  create:       (data)   => api.post('/reviews', data),
  myReviews:    ()       => api.get('/reviews/me'),
  vendorReviews:(id, params) => api.get(`/reviews/vendors/${id}`, { params }),
  vendorStats:  (id)     => api.get(`/reviews/vendors/${id}/stats`),
  update:       (id, data) => api.patch(`/reviews/${id}`, data),
  reply:        (id, data) => api.post(`/reviews/${id}/reply`, data),
  deleteReply:  (id)     => api.delete(`/reviews/${id}/reply`),
  moderate:     (id, data) => api.post(`/reviews/${id}/moderate`, data),
}

// ── Admin ──────────────────────────────────────────────────────────────────────
export const adminApi = {
  auditLogs: (params) => api.get('/admin/audit-logs', { params }),
}

export default api