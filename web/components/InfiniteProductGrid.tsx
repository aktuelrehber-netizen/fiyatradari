'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import Image from 'next/image'
import { TrendingDown } from 'lucide-react'

interface Product {
  id: number
  asin: string
  title: string
  brand?: string
  current_price: string
  list_price?: string
  image_url?: string
  detail_page_url?: string
  rating?: number
  review_count?: number
}

interface InfiniteProductGridProps {
  initialProducts: Product[]
  categoryId: number
  totalProducts: number
}

export default function InfiniteProductGrid({
  initialProducts,
  categoryId,
  totalProducts
}: InfiniteProductGridProps) {
  const [products, setProducts] = useState<Product[]>(initialProducts)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [hasMore, setHasMore] = useState(initialProducts.length < totalProducts)
  const observerTarget = useRef<HTMLDivElement>(null)

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return

    setLoading(true)
    try {
      const response = await fetch(
        `/api/v1/products?category_id=${categoryId}&skip=${page * 50}&limit=50`
      )
      const data = await response.json()
      const newProducts = data.items || []

      if (newProducts.length === 0) {
        setHasMore(false)
      } else {
        setProducts(prev => [...prev, ...newProducts])
        setPage(prev => prev + 1)
        setHasMore(products.length + newProducts.length < totalProducts)
      }
    } catch (error) {
      console.error('Failed to load more products:', error)
    } finally {
      setLoading(false)
    }
  }, [categoryId, page, loading, hasMore, totalProducts, products.length])

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore()
        }
      },
      { threshold: 0.1 }
    )

    const currentTarget = observerTarget.current
    if (currentTarget) {
      observer.observe(currentTarget)
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget)
      }
    }
  }, [loadMore, hasMore, loading])

  if (products.length === 0) {
    return (
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
    )
  }

  return (
    <>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-gray-800">
          Aktif Fırsatlar
        </h2>
        <p className="text-sm text-gray-600">
          {products.length} / {totalProducts} ürün gösteriliyor
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {products.map((product) => {
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
                    {product.review_count && (
                      <span className="text-gray-500">
                        ({product.review_count})
                      </span>
                    )}
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
                <a
                  href={product.detail_page_url || `https://www.amazon.com.tr/dp/${product.asin}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full bg-[#FF9900] hover:bg-[#FF9900]/90 text-white text-center py-2 rounded-lg text-sm font-semibold transition-all hover:shadow-lg active:scale-95"
                >
                  Satın Al
                </a>
              </div>
            </div>
          )
        })}
      </div>

      {/* Loading indicator and observer target */}
      <div ref={observerTarget} className="flex justify-center py-8">
        {loading && (
          <div className="flex items-center gap-2 text-gray-600">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#FF9900]"></div>
            <span className="text-sm">Daha fazla ürün yükleniyor...</span>
          </div>
        )}
        {!hasMore && products.length > 0 && (
          <div className="text-sm text-gray-500">
            Tüm ürünler gösterildi
          </div>
        )}
      </div>
    </>
  )
}
