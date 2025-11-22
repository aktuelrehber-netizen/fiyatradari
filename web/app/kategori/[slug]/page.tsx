import { api } from '@/utils/api'
import { ExternalLink } from 'lucide-react'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { Metadata } from 'next'
import InfiniteProductGrid from '@/components/InfiniteProductGrid'

// ISR: Revalidate every 30 seconds (faster updates when ratings change)
export const revalidate = 30

interface PageProps {
  params: Promise<{
    slug: string
  }>
}

interface Category {
  id: number
  name: string
  slug: string
  description?: string | null
  meta_title?: string | null
  meta_description?: string | null
  parent_id?: number | null
  children?: Category[]
}

// Generate metadata from database
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params
  
  try {
    const category = await api.getCategoryBySlug(slug)
    
    if (!category) {
      return {
        title: 'Kategori Bulunamadı',
      }
    }

    return {
      title: category.meta_title || `${category.name} Fırsatları`,
      description: category.meta_description || category.description || `${category.name} kategorisindeki en iyi Amazon fırsatlarını keşfedin. Günlük güncellenen indirimler!`,
      openGraph: {
        title: category.meta_title || `${category.name} Fırsatları | Fiyat Radarı`,
        description: category.meta_description || category.description || `${category.name} kategorisindeki en iyi Amazon fırsatlarını keşfedin.`,
        type: 'website',
        url: `https://fiyatradari.com/kategori/${category.slug}`,
      },
      twitter: {
        card: 'summary_large_image',
        title: category.meta_title || `${category.name} Fırsatları`,
        description: category.meta_description || category.description || `${category.name} kategorisindeki en iyi Amazon fırsatlarını keşfedin.`,
      },
      alternates: {
        canonical: `https://fiyatradari.com/kategori/${category.slug}`,
      },
    }
  } catch (error) {
    return {
      title: 'Kategori Bulunamadı',
    }
  }
}

export default async function CategoryPage({ params }: PageProps) {
  const { slug } = await params
  
  // Fetch category, products, and all categories for tree
  let category: Category | null = null
  let initialProducts: any[] = []
  let totalProducts: number = 0
  let allCategories: Category[] = []
  let subcategories: Category[] = []
  
  try {
    const [categoryResponse, allCategoriesResponse] = await Promise.all([
      api.getCategoryBySlug(slug),
      api.getCategories()
    ])
    
    category = categoryResponse
    allCategories = allCategoriesResponse || []
    
    if (category) {
      // Find subcategories (direct children)
      const catId = category.id
      subcategories = allCategories.filter((cat: Category) => cat.parent_id === catId)
      
      // Get initial 50 products for infinite scroll
      const response = await api.getProductsByCategory(category.id, { limit: 50 })
      initialProducts = response.items || response || []
      totalProducts = response.total || initialProducts.length
    }
  } catch (error) {
    // Silent fail - show 404 page
    notFound()
  }

  if (!category) {
    notFound()
  }

  return (
    <main className="min-h-screen bg-[#F7F7F7]">
      {/* Category Header - Modern & Compact */}
      <section className="border-b border-gray-100 bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6 md:py-8">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">{category.name}</h1>
            {category.description && (
              <p className="text-sm md:text-base text-gray-600 max-w-3xl">
                {category.description}
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Subcategories */}
      {subcategories.length > 0 && (
        <section className="container mx-auto px-4 py-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Alt Kategoriler</h2>
          <div className="bg-white rounded-xl p-4 md:p-6 shadow-sm border border-gray-100">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {subcategories.map((subcat) => (
                <Link
                  key={subcat.id}
                  href={`/kategori/${subcat.slug}`}
                  className="group flex items-center gap-2 px-4 py-3 bg-gray-50 hover:bg-[#FF9900]/10 border border-gray-200 hover:border-[#FF9900]/30 rounded-lg transition-all"
                >
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900 group-hover:text-[#FF9900] transition-colors">
                      {subcat.name}
                    </div>
                  </div>
                  <ExternalLink className="h-3.5 w-3.5 text-gray-400 group-hover:text-[#FF9900] transition-colors" />
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Products Grid - Always show products with infinite scroll */}
      <section className="container mx-auto px-4 py-8">
        <InfiniteProductGrid
          initialProducts={initialProducts}
          categoryId={category.id}
          totalProducts={totalProducts}
        />
      </section>
    </main>
  )
}
