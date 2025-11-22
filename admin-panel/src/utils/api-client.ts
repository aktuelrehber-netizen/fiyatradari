import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token')
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
  
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },
}

// Categories API
export const categoriesAPI = {
  list: async (params?: any) => {
    const response = await apiClient.get('/categories/', { params })
    return response.data
  },
  
  get: async (id: number) => {
    const response = await apiClient.get(`/categories/${id}`)
    return response.data
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/categories/', data)
    return response.data
  },
  
  update: async (id: number, data: any) => {
    const response = await apiClient.put(`/categories/${id}`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await apiClient.delete(`/categories/${id}`)
    return response.data
  },
  
  fetchProducts: async (id: number) => {
    const response = await apiClient.post(`/categories/${id}/fetch-products`)
    return response.data
  },
}

// Products API
export const productsAPI = {
  list: async (params?: any) => {
    const response = await apiClient.get('/products/', { params })
    return response.data
  },
  
  get: async (id: number) => {
    const response = await apiClient.get(`/products/${id}`)
    return response.data
  },
  
  getByAsin: async (asin: string) => {
    const response = await apiClient.get(`/products/asin/${asin}`)
    return response.data
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/products/', data)
    return response.data
  },
  
  update: async (id: number, data: any) => {
    const response = await apiClient.put(`/products/${id}`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await apiClient.delete(`/products/${id}`)
    return response.data
  },
  
  toggleActive: async (id: number) => {
    const response = await apiClient.patch(`/products/${id}`, {})
    return response.data
  },
  
  getPriceHistory: async (id: number, days: number = 30) => {
    const response = await apiClient.get(`/products/${id}/price-history`, {
      params: { days }
    })
    return response.data
  },
}

// Deals API
export const dealsAPI = {
  list: async (params?: any) => {
    const response = await apiClient.get('/deals/', { params })
    return response.data
  },
  
  get: async (id: number) => {
    const response = await apiClient.get(`/deals/${id}`)
    return response.data
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/deals/', data)
    return response.data
  },
  
  update: async (id: number, data: any) => {
    const response = await apiClient.put(`/deals/${id}`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await apiClient.delete(`/deals/${id}`)
    return response.data
  },
  
  publish: async (id: number) => {
    const response = await apiClient.post(`/deals/${id}/publish`)
    return response.data
  },
  
  unpublish: async (id: number) => {
    const response = await apiClient.post(`/deals/${id}/unpublish`)
    return response.data
  },
}

// Settings API
export const settingsAPI = {
  list: async (group?: string) => {
    const response = await apiClient.get('/settings/', {
      params: group ? { group } : {}
    })
    return response.data
  },
  
  get: async (key: string) => {
    const response = await apiClient.get(`/settings/${key}`)
    return response.data
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/settings/', data)
    return response.data
  },
  
  update: async (key: string, data: any) => {
    const response = await apiClient.put(`/settings/${key}`, data)
    return response.data
  },
  
  delete: async (key: string) => {
    const response = await apiClient.delete(`/settings/${key}`)
    return response.data
  },
  
  getWorkerLogs: async (params?: any) => {
    const response = await apiClient.get('/settings/worker/logs', { params })
    return response.data
  },
}

// Health API
export const healthAPI = {
  check: async () => {
    const response = await apiClient.get('/health/')
    return response.data
  },
  
  dashboard: async () => {
    const response = await apiClient.get('/health/dashboard')
    return response.data
  },
  
  services: async () => {
    const response = await apiClient.get('/health/services')
    return response.data
  },
  
  getTrends: async () => {
    const response = await apiClient.get('/health/analytics/trends')
    return response.data
  },
  
  getCategoryStats: async () => {
    const response = await apiClient.get('/health/analytics/categories')
    return response.data
  },
  
  getTopDeals: async () => {
    const response = await apiClient.get('/health/analytics/top-deals')
    return response.data
  },
  
  getRecentProducts: async () => {
    const response = await apiClient.get('/health/analytics/recent-products')
    return response.data
  },
}

// Users API
export const usersAPI = {
  list: async (params?: any) => {
    const response = await apiClient.get('/users/', { params })
    return response.data
  },
  
  get: async (id: number) => {
    const response = await apiClient.get(`/users/${id}`)
    return response.data
  },
  
  create: async (data: any) => {
    const response = await apiClient.post('/users/', data)
    return response.data
  },
  
  update: async (id: number, data: any) => {
    const response = await apiClient.put(`/users/${id}`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    const response = await apiClient.delete(`/users/${id}`)
    return response.data
  },
}

// Workers API
export const workersAPI = {
  getStatus: async () => {
    const response = await apiClient.get('/workers/status')
    return response.data
  },
  
  getLogs: async (params?: any) => {
    const response = await apiClient.get('/workers/logs', { params })
    return response.data
  },
  
  getLog: async (id: number) => {
    const response = await apiClient.get(`/workers/logs/${id}`)
    return response.data
  },
  
  getStatistics: async (days: number = 7) => {
    const response = await apiClient.get('/workers/statistics/overview', {
      params: { days }
    })
    return response.data
  },
  
  getProgress: async () => {
    const response = await apiClient.get('/workers/progress')
    return response.data
  },
  
  triggerJob: async (jobType: string) => {
    const response = await apiClient.post(`/workers/trigger/${jobType}`)
    return response.data
  },
  
  pauseScheduler: async () => {
    const response = await apiClient.post('/workers/control/pause')
    return response.data
  },
  
  resumeScheduler: async () => {
    const response = await apiClient.post('/workers/control/resume')
    return response.data
  },
  
  enableJob: async (jobType: string) => {
    const response = await apiClient.post(`/workers/control/job/${jobType}/enable`)
    return response.data
  },
  
  disableJob: async (jobType: string) => {
    const response = await apiClient.post(`/workers/control/job/${jobType}/disable`)
    return response.data
  },
  
  getControlStatus: async () => {
    const response = await apiClient.get('/workers/control/status')
    return response.data
  },
}

// Amazon API
export const amazonAPI = {
  searchBrowseNodes: async (keyword: string) => {
    const response = await apiClient.post('/amazon/search-browse-nodes', { keyword })
    return response.data
  },
}

// System Management API
export const systemAPI = {
  getDashboard: async () => {
    const response = await apiClient.get('/system/dashboard')
    return response.data
  },
  
  getWorkerPool: async () => {
    const response = await apiClient.get('/system/workers/pool')
    return response.data
  },
  
  scaleWorkerPool: async (size: number) => {
    const response = await apiClient.post(`/system/workers/pool/scale?size=${size}`)
    return response.data
  },
  
  getSchedules: async () => {
    const response = await apiClient.get('/system/schedules')
    return response.data
  },
  
  updateSchedule: async (jobType: string, enabled: boolean, cron: string) => {
    const response = await apiClient.post(
      `/system/schedules/${jobType}?enabled=${enabled}&cron=${encodeURIComponent(cron)}`
    )
    return response.data
  },
  
  getActiveTasks: async () => {
    const response = await apiClient.get('/system/tasks/active')
    return response.data
  },
  
  cancelTask: async (taskId: string) => {
    const response = await apiClient.post(`/system/tasks/${taskId}/cancel`)
    return response.data
  },
  
  pauseAll: async () => {
    const response = await apiClient.post('/system/control/pause')
    return response.data
  },
  
  resumeAll: async () => {
    const response = await apiClient.post('/system/control/resume')
    return response.data
  },
  
  getControlStatus: async () => {
    const response = await apiClient.get('/system/control/status')
    return response.data
  },
  
  restartWorkers: async () => {
    const response = await apiClient.post('/system/workers/restart')
    return response.data
  },
}
