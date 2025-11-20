import { MetadataRoute } from 'next'
import { api } from '@/utils/api'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://fiyatradari.com'
  
  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1.0,
    },
    {
      url: `${baseUrl}/hakkimizda`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.5,
    },
    {
      url: `${baseUrl}/iletisim`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.5,
    },
  ]

  // Fetch categories only (we don't have product detail pages)
  let categoryPages: MetadataRoute.Sitemap = []
  try {
    const categories = await api.getCategories()
    categoryPages = categories.map((category: any) => ({
      url: `${baseUrl}/kategori/${category.slug}`,
      lastModified: new Date(category.updated_at || category.created_at),
      changeFrequency: 'daily' as const,
      priority: 0.8,
    }))
  } catch (error) {
    console.error('Failed to fetch categories for sitemap:', error)
  }

  return [...staticPages, ...categoryPages]
}
