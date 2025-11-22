import { api } from '@/utils/api'
import { ExternalLink, TrendingDown } from 'lucide-react'
import Image from 'next/image'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { Metadata } from 'next'

// ISR: Revalidate every 120 seconds (categories change less frequently)
export const revalidate = 120

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
  let deals: any[] = []
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
      
      // Always get products for the category (and its subcategories)
      const response = await api.getProductsByCategory(category.id, { limit: 10000 })
      deals = response.items || response || []
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
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h1 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">{category.name}</h1>
              {category.description && (
                <p className="text-sm md:text-base text-gray-600 max-w-3xl">
                  {category.description}
                </p>
              )}
            </div>
            {(subcategories.length > 0 || deals.length > 0) && (
              <div className="flex-shrink-0 text-right">
                <div className="inline-flex flex-col items-end bg-gradient-to-br from-[#FF9900]/10 to-[#242F3E]/10 px-4 py-3 rounded-xl border border-[#FF9900]/30">
                  {subcategories.length > 0 ? (
                    <>
                      <span className="text-xl md:text-2xl font-bold text-[#FF9900]">{subcategories.length}</span>
                      <span className="text-xs text-gray-600 mt-0.5">Alt Kategori</span>
                    </>
                  ) : (
                    <>
                      <span className="text-xl md:text-2xl font-bold text-[#FF9900]">{deals.length}</span>
                      <span className="text-xs text-gray-600 mt-0.5">Aktif Fırsat</span>
                    </>
                  )}
                </div>
              </div>
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

      {/* Products Grid - Always show products */}
      <section className="container mx-auto px-4 py-8">
        {deals.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <div className="text-4xl mb-3">📦</div>
            <h2 className="text-md font-bold text-gray-800 mb-2">
              Henüz Fırsat Yok
            </h2>
            <p className="text-xs text-gray-600 mb-4">
              Bu kategoride şu anda aktif fırsat bulunmuyor. Telegram kanalımıza katılarak yeni fırsatlardan haberdar olun!
            </p>
            <a
              href="https://t.me/firsatradaricom"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-[#FF9900] hover:bg-[#FF9900]/90 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg transition-all hover:scale-105"
            >
              Telegram'a Katıl
            </a>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-800">
                Aktif Fırsatlar
              </h2>
              <p className="text-sm text-gray-600">
                {deals.length} ürün bulundu
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {deals.map((product: any) => {
                const discountPercentage = product.list_price && product.current_price
                  ? ((parseFloat(product.list_price) - parseFloat(product.current_price)) / parseFloat(product.list_price) * 100)
                  : 0

                return (
                  <div
                    key={product.id}
                    className="bg-white rounded-xl border border-gray-200 hover:shadow-xl hover:border-[#FF9900]/30 transition-all duration-300 overflow-hidden group"
                  >
                    {/* Image */}
                    <div className="relative aspect-square bg-gradient-to-br from-gray-50 to-gray-100 overflow-hidden">
                      {product.image_url && (
                        <Image
                          src={product.image_url}
                          alt={product.title}
                          fill
                          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                          className="object-contain p-4 group-hover:scale-110 transition-transform duration-500"
                        />
                      )}
                      {discountPercentage > 0 && (
                        <div className="absolute top-2 right-2 bg-[#FF9900] text-white px-2 py-1 rounded-lg font-bold text-xs flex items-center gap-1 shadow-lg">
                          <TrendingDown className="h-3 w-3" />
                          %{discountPercentage.toFixed(0)}
                        </div>
                      )}
                    </div>

                    {/* Details */}
                    <div className="p-3">
                      {/* Brand */}
                      {product.brand && (
                        <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">
                          {product.brand}
                        </div>
                      )}

                      {/* Title */}
                      <h3 className="font-semibold text-sm text-gray-800 mb-2 line-clamp-2 leading-tight">
                        {product.title}
                      </h3>

                      {/* Rating */}
                      {product.rating && (
                        <div className="flex items-center gap-1.5 mb-2 text-xs">
                          <div className="flex items-center">
                            <span className="text-yellow-500">★</span>
                            <span className="ml-0.5 font-medium">{product.rating}</span>
                          </div>
                          <span className="text-gray-500">
                            ({product.review_count})
                          </span>
                        </div>
                      )}

                      {/* Prices */}
                      <div className="mb-3">
                        <div className="text-xl font-bold text-green-600">
                          {parseFloat(product.current_price).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                        </div>
                        {product.list_price && parseFloat(product.list_price) > parseFloat(product.current_price) && (
                          <div className="text-xs text-gray-400 line-through">
                            {parseFloat(product.list_price).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                          </div>
                        )}
                      </div>

                      {/* Amazon Link */}
                      {product.detail_page_url && (
                        <a
                          href={product.detail_page_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block w-full bg-[#FF9900] hover:bg-[#FF9900]/90 text-white text-center py-2 rounded-lg text-sm font-semibold transition-all hover:shadow-lg active:scale-95"
                        >
                          Satın Al
                        </a>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </section>
    </main>
  )
}
