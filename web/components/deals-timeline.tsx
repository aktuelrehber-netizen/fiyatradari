'use client'

import { TrendingDown, Clock, ExternalLink } from 'lucide-react'
import Image from 'next/image'

interface Deal {
  id: number
  title: string
  description?: string
  original_price: string
  deal_price: string
  discount_percentage: number
  currency: string
  created_at: string
  product?: {
    image_url?: string
    detail_page_url?: string
    brand?: string
  }
}

interface DealsTimelineProps {
  deals: Deal[]
}

export function DealsTimeline({ deals }: DealsTimelineProps) {
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 60) return `${minutes} dakika önce`
    if (hours < 24) return `${hours} saat önce`
    return `${days} gün önce`
  }

  return (
    <div className="container mx-auto px-4 py-12">
      {/* Section Header */}
      <div className="text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-bold text-gray-800 mb-4">
          ⚡ Son İndirimler
        </h2>
        <p className="text-gray-600">
          Amazon'dan tespit edilen en yeni fırsatlar
        </p>
      </div>

      {/* Timeline */}
      <div className="max-w-5xl mx-auto">
        <div className="relative">
          {/* Timeline Line */}
          <div className="absolute left-4 md:left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-orange-200 via-orange-300 to-orange-100" />

          {/* Timeline Items */}
          <div className="space-y-8">
            {deals.map((deal, index) => {
              const isEven = index % 2 === 0

              return (
                <div
                  key={deal.id}
                  className={`relative flex items-center ${
                    isEven ? 'md:flex-row' : 'md:flex-row-reverse'
                  } gap-8`}
                >
                  {/* Timeline Dot */}
                  <div className="absolute left-4 md:left-1/2 md:-translate-x-1/2 w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center shadow-lg z-10">
                    <TrendingDown className="h-4 w-4 text-white" />
                  </div>

                  {/* Content Card */}
                  <div className={`flex-1 ml-16 md:ml-0 ${isEven ? 'md:pr-12' : 'md:pl-12'}`}>
                    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow p-6 border border-gray-100">
                      <div className="flex gap-4">
                        {/* Image */}
                        {deal.product?.image_url && (
                          <div className="flex-shrink-0 w-24 h-24 bg-gray-100 rounded-lg overflow-hidden">
                            <Image
                              src={deal.product.image_url}
                              alt={deal.title}
                              width={96}
                              height={96}
                              className="object-contain w-full h-full p-2"
                            />
                          </div>
                        )}

                        {/* Details */}
                        <div className="flex-1 min-w-0">
                          {/* Time */}
                          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                            <Clock className="h-4 w-4" />
                            <span>{formatTimeAgo(deal.created_at)}</span>
                          </div>

                          {/* Brand */}
                          {deal.product?.brand && (
                            <div className="text-sm text-gray-600 mb-1">
                              {deal.product.brand}
                            </div>
                          )}

                          {/* Title */}
                          <h3 className="font-semibold text-gray-800 mb-2 line-clamp-2">
                            {deal.title}
                          </h3>

                          {/* Prices */}
                          <div className="flex items-baseline gap-3 mb-3">
                            <span className="text-2xl font-bold text-green-600">
                              {parseFloat(deal.deal_price).toFixed(2)} {deal.currency}
                            </span>
                            <span className="text-sm text-gray-400 line-through">
                              {parseFloat(deal.original_price).toFixed(2)} {deal.currency}
                            </span>
                            <span className="bg-orange-500 text-white px-2 py-1 rounded-full text-sm font-bold">
                              %{deal.discount_percentage.toFixed(0)} İndirim
                            </span>
                          </div>

                          {/* Amazon Link */}
                          {deal.product?.detail_page_url && (
                            <a
                              href={deal.product.detail_page_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 text-orange-500 hover:text-orange-600 font-medium text-sm"
                            >
                              Amazon'da Gör
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Spacer for desktop */}
                  <div className="hidden md:block flex-1" />
                </div>
              )
            })}
          </div>
        </div>

        {/* No deals message */}
        {deals.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">Henüz fırsat tespit edilmedi.</p>
            <p className="text-sm mt-2">Telegram kanalımıza katılarak ilk bildirimi al!</p>
          </div>
        )}
      </div>
    </div>
  )
}
