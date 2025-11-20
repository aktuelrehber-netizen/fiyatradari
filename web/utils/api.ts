import axios from 'axios'

// Server-side: use docker network, Client-side: use environment variable
const getApiUrl = () => {
  if (typeof window === 'undefined') {
    // Server-side in Docker
    return process.env.NEXT_PRIVATE_API_URL || 'http://backend:8000'
  }
  // Client-side in browser
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}

// Create fresh axios instance for each request
const getApiClient = () => {
  return axios.create({
    baseURL: `${getApiUrl()}/api/v1`,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 10000,
  })
}

// API functions
export const api = {
  // Get active deals
  getDeals: async (params?: { skip?: number; limit?: number }) => {
    const response = await getApiClient().get('/deals/', {
      params: { ...params, is_active: true, is_published: true }
    })
    return response.data
  },

  // Get categories
  getCategories: async () => {
    const response = await getApiClient().get('/categories/', {
      params: { is_active: true }
    })
    return response.data
  },

  // Get category by slug
  getCategoryBySlug: async (slug: string) => {
    const response = await getApiClient().get(`/categories/slug/${slug}`)
    return response.data
  },

  // Get products by category
  getProductsByCategory: async (categoryId: number, params?: { skip?: number; limit?: number }) => {
    const response = await getApiClient().get('/products/', {
      params: { category_id: categoryId, is_active: true, ...params }
    })
    return response.data
  },
}
