import Link from 'next/link'
import Image from 'next/image'
import { api } from '@/utils/api'
import { TrendingDown, ExternalLink, Send, Zap, Bell, Tag, Sparkles, Clock, Shield, TrendingUp } from 'lucide-react'

// ISR: Revalidate every 30 seconds (faster updates when ratings change)
export const revalidate = 30

// Amazon Affiliate Tag
const AMAZON_PARTNER_TAG = 'firsatradar06-21'

// Generate Amazon affiliate link
function getAmazonLink(product: any): string {
  if (!product) return '#'
  
  // If detail_page_url exists, add partner tag
  if (product.detail_page_url) {
    const url = product.detail_page_url
    const separator = url.includes('?') ? '&' : '?'
    return `${url}${separator}tag=${AMAZON_PARTNER_TAG}`
  }
  
  // Otherwise, generate from ASIN
  if (product.asin) {
    return `https://www.amazon.com.tr/dp/${product.asin}?tag=${AMAZON_PARTNER_TAG}`
  }
  
  return '#'
}

export default async function Home() {
  let deals = []
  let categories = []
  
  try {
    const [dealsResponse, categoriesResponse] = await Promise.allSettled([
      api.getDeals({ limit: 8 }),
      api.getCategories()
    ])
    
    if (dealsResponse.status === 'fulfilled') {
      deals = dealsResponse.value.items || dealsResponse.value || []
    }
    if (categoriesResponse.status === 'fulfilled') {
      categories = categoriesResponse.value || []
    }
  } catch (error) {
    // Silent fail - page will show empty states
  }

  // Get only parent categories
  const parentCategories = categories.filter((cat: any) => !cat.parent_id).slice(0, 8)

  return (
    <main className="min-h-screen bg-[#F7F7F7]">
      {/* Modern Compact Hero */}
      <section className="relative overflow-hidden bg-white">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] -z-10" />
        
        <div className="container mx-auto px-4 py-6 md:py-8">
          <div className="max-w-6xl mx-auto">
            
            {/* Main Content */}
            <div className="text-center mb-4 py-4">
              <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-2 leading-tight tracking-tight">
                Gerçek İndirimleri
                <span className="block text-transparent bg-clip-text bg-gradient-to-r from-[#FF9900] to-[#242F3E] text-3xl md:text-4xl">
                  Fiyat Radarı ile Anında Yakalayın!
                </span>
              </h1>
              
              <p className="text-sm md:text-base text-gray-600 max-w-2xl mx-auto mb-4">
                Amazon'daki en iyi indirimleri sizler için anlık takip ediyoruz.
              </p>
              
              {/* CTA Button */}
              <div className="flex justify-center">
                <a
                  href="https://t.me/firsatradaricom"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group relative inline-flex items-center justify-center gap-2 bg-[#FF9900] hover:bg-[#FF9900]/90 text-white px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all hover:scale-[1.02] active:scale-95"
                >
                  <Send className="h-4 w-4 relative z-10" />
                  <span className="relative z-10">Telegram'a Katıl</span>
                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Deals */}
      <section id="firsatlar" className="py-8 md:py-12">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg md:text-xl font-bold text-gray-900">🔥 Son Fırsatlar</h2>
              <p className="text-xs md:text-sm text-gray-500 mt-0.5">Şimdi al, pişman olma!</p>
            </div>
            <Link
              href="/firsatlar"
              className="text-xs md:text-sm text-[#FF9900] hover:text-[#FF9900]/80 font-semibold flex items-center gap-1"
            >
              Tümü
              <ExternalLink className="h-3 w-3" />
            </Link>
          </div>

          {deals.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-2xl border border-gray-100 shadow-sm">
              <div className="text-6xl mb-4">🎁</div>
              <h3 className="text-base font-bold text-gray-800 mb-2">Fırsatlar Yolda!</h3>
              <p className="text-sm text-gray-600 mb-6 max-w-sm mx-auto">
                Yeni fırsatları ilk sen öğren. Telegram'da bildirimler aç!
              </p>
              <a
                href="https://t.me/firsatradaricom"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-[#FF9900] hover:bg-[#FF9900]/90 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg transition-all hover:scale-105"
              >
                <Bell className="h-4 w-4" />
                Bildirimleri Aç
              </a>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
              {deals.map((deal: any) => {
                const discountPercentage = deal.discount_percentage || 0
                
                // Calculate time since published
                const getTimeBadge = () => {
                  if (!deal.published_at && !deal.created_at) return null
                  
                  const publishedDate = new Date(deal.published_at || deal.created_at)
                  const now = new Date()
                  const hoursSince = (now.getTime() - publishedDate.getTime()) / (1000 * 60 * 60)
                  
                  if (hoursSince < 2) {
                    return { text: '⚡ YENİ', className: 'bg-green-500 animate-pulse' }
                  } else if (hoursSince < 12) {
                    return { text: '🔥 BUGÜN', className: 'bg-red-500' }
                  }
                  return null
                }
                
                const timeBadge = getTimeBadge()
                
                // Get "cheapest" badge
                const getCheapestBadge = () => {
                  if (deal.is_cheapest_6months) {
                    return { text: '🏆 6 AYIN EN UCUZU', className: 'bg-purple-600', icon: '👑' }
                  } else if (deal.is_cheapest_3months) {
                    return { text: '⭐ 3 AYIN EN UCUZU', className: 'bg-indigo-600', icon: '⭐' }
                  } else if (deal.is_cheapest_1month) {
                    return { text: '💎 AYIN EN UCUZU', className: 'bg-blue-600', icon: '💎' }
                  } else if (deal.is_cheapest_14days) {
                    return { text: '✨ 14 GÜNÜN EN UCUZU', className: 'bg-cyan-600', icon: '✨' }
                  }
                  return null
                }
                
                const cheapestBadge = getCheapestBadge()
                
                return (
                  <div
                    key={deal.id}
                    className="group bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-xl hover:border-[#FF9900]/30 transition-all duration-300"
                  >
                    {/* Image */}
                    <div className="relative aspect-square bg-gradient-to-br from-gray-50 to-gray-100 overflow-hidden">
                      {deal.product?.image_url && (
                        <Image
                          src={deal.product.image_url}
                          alt={deal.title}
                          fill
                          sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
                          className="object-contain p-4 group-hover:scale-110 transition-transform duration-500"
                        />
                      )}
                      
                      {/* Cheapest Badge - Top (Full Width) */}
                      {cheapestBadge && (
                        <div className={`absolute top-2 left-2 right-2 ${cheapestBadge.className} text-white px-2 py-1.5 rounded-lg font-bold text-[9px] md:text-[10px] shadow-xl text-center border-2 border-white/20 backdrop-blur-sm`}>
                          <span className="mr-1">{cheapestBadge.icon}</span>
                          {cheapestBadge.text}
                        </div>
                      )}
                      
                      {/* Time Badge - Below Cheapest or Top Left */}
                      {timeBadge && (
                        <div className={`absolute ${cheapestBadge ? 'top-12' : 'top-2'} left-2 ${timeBadge.className} text-white px-2 py-1 rounded-lg font-bold text-[10px] md:text-xs shadow-lg`}>
                          {timeBadge.text}
                        </div>
                      )}
                      
                      {/* Discount Badge - Top Right */}
                      {discountPercentage > 0 && (
                        <div className={`absolute ${cheapestBadge ? 'top-12' : 'top-2'} right-2 bg-[#FF9900] text-white px-2 py-1 rounded-lg font-bold text-[10px] md:text-xs flex items-center gap-1 shadow-lg`}>
                          <TrendingDown className="h-3 w-3" />
                          <span>%{discountPercentage.toFixed(0)}</span>
                        </div>
                      )}
                      {deal.product?.brand && (
                        <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur-sm px-2 py-0.5 rounded-md text-[9px] md:text-[10px] font-semibold text-gray-700 uppercase tracking-wide shadow-sm">
                          {deal.product.brand}
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <div className="p-3">
                      <h3 className="font-semibold text-xs md:text-sm text-gray-800 mb-2 line-clamp-2 leading-tight">
                        {deal.title}
                      </h3>

                      {/* Price */}
                      <div className="mb-2">
                        <div className="mb-0.5">
                          <span className="text-lg md:text-xl font-bold text-emerald-600">
                            {parseFloat(deal.deal_price).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                          </span>
                        </div>
                        
                        {/* Price comparison with previous price */}
                        {deal.previous_price && parseFloat(deal.previous_price) > parseFloat(deal.deal_price) && (
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-[10px] md:text-xs text-gray-400 line-through">
                              {parseFloat(deal.previous_price).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                            </span>
                            <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-semibold flex items-center gap-0.5">
                              <TrendingDown className="h-2.5 w-2.5" />
                              -{discountPercentage.toFixed(0)}%
                            </span>
                          </div>
                        )}
                        
                        {/* Fallback to original_price if no previous_price */}
                        {!deal.previous_price && deal.original_price && parseFloat(deal.original_price) > parseFloat(deal.deal_price) && (
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] md:text-xs text-gray-400 line-through">
                              {parseFloat(deal.original_price).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺
                            </span>
                            <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-semibold">
                              -{discountPercentage.toFixed(0)}%
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Amazon Link */}
                      {deal.product && (
                        <a
                          href={getAmazonLink(deal.product)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block w-full bg-[#FF9900] hover:bg-[#FF9900]/90 text-white text-center py-2 rounded-lg text-xs md:text-sm font-semibold transition-all hover:shadow-lg active:scale-95"
                        >
                          Satın Al →
                        </a>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </section>

      {/* CTA Section - Compact Modern */}
      <section className="relative overflow-hidden bg-white py-12 md:py-16">
        {/* Decorative Elements */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        
        <div className="container mx-auto px-4 relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            {/* Icon */}
            <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-[#FF9900] to-[#FF7700] rounded-2xl mb-4 shadow-lg">
              <Send className="h-7 w-7 text-white" />
            </div>
            
            <h2 className="text-xl md:text-3xl font-bold text-gray-900 mb-3 tracking-tight">
              Hiçbir Fırsatı Kaçırma! 🎯
            </h2>
            <p className="text-sm md:text-base text-gray-600 mb-6 max-w-xl mx-auto">
              Telegram'a katıl, en iyi fırsatları ilk sen öğren. Tamamen ücretsiz! ⚡
            </p>
            
            <a
              href="https://t.me/firsatradaricom"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 bg-[#FF9900] hover:bg-[#FF9900]/90 text-white px-6 md:px-8 py-3 md:py-3.5 rounded-xl font-bold text-sm md:text-base transition-all hover:scale-105 shadow-lg active:scale-95 group"
            >
              <Send className="h-4 w-4 group-hover:rotate-12 transition-transform" />
              <span>Ücretsiz Katıl</span>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            </a>
            
            {/* Features - Compact */}
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4 md:gap-6">
              {[
                { icon: Bell, text: 'Anlık Bildirim' },
                { icon: Shield, text: '100% Güvenli' },
                { icon: Zap, text: 'Tamamen Ücretsiz' }
              ].map((feature, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-gray-100 px-3 py-1.5 rounded-full">
                  <feature.icon className="h-3 w-3 text-[#FF9900]" />
                  <span className="text-xs font-medium text-gray-700">{feature.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  )
}
