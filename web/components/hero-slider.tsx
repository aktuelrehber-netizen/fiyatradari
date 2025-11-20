'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ChevronLeft, ChevronRight, Send, Bell, Zap } from 'lucide-react'

const slides = [
  {
    id: 1,
    title: 'Amazon\'dan En İyi Fırsatları Kaçırma!',
    description: 'Telegram kanalımıza katıl, anlık indirim bildirimleri al',
    icon: Send,
    bgColor: 'from-blue-500 to-blue-600',
    cta: 'Telegram\'a Katıl',
    ctaLink: 'https://t.me/firsatradaricom'
  },
  {
    id: 2,
    title: '⚡ Anlık İndirim Bildirimleri',
    description: 'Fırsatlar yayınlanır yayınlanmaz haberdar ol',
    icon: Bell,
    bgColor: 'from-purple-500 to-purple-600',
    cta: 'Hemen Başla',
    ctaLink: 'https://t.me/firsatradaricom'
  },
  {
    id: 3,
    title: '🔥 Günlük Onlarca Fırsat',
    description: 'Her gün yeni indirimler, özel teklifler',
    icon: Zap,
    bgColor: 'from-orange-500 to-red-500',
    cta: 'Katıl',
    ctaLink: 'https://t.me/firsatradaricom'
  },
]

export function HeroSlider() {
  const [currentSlide, setCurrentSlide] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length)
    }, 5000) // Her 5 saniyede değiştir

    return () => clearInterval(timer)
  }, [])

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length)
  }

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length)
  }

  const slide = slides[currentSlide]
  const Icon = slide.icon

  return (
    <div className="relative bg-gradient-to-r overflow-hidden">
      <div className={`bg-gradient-to-r ${slide.bgColor} transition-all duration-500`}>
        <div className="container mx-auto px-4 py-16 md:py-24">
          <div className="max-w-4xl mx-auto text-center text-white">
            {/* Icon */}
            <div className="mb-6 flex justify-center">
              <div className="bg-white/20 p-4 rounded-full backdrop-blur-sm">
                <Icon className="h-12 w-12 md:h-16 md:w-16" />
              </div>
            </div>

            {/* Title */}
            <h1 className="text-3xl md:text-5xl font-bold mb-4 animate-fade-in">
              {slide.title}
            </h1>

            {/* Description */}
            <p className="text-lg md:text-xl mb-8 text-white/90">
              {slide.description}
            </p>

            {/* CTA Button */}
            <Link
              href={slide.ctaLink}
              target="_blank"
              className="inline-flex items-center gap-2 bg-white text-gray-900 px-8 py-4 rounded-full font-semibold text-lg hover:bg-gray-100 transition-all hover:scale-105 shadow-lg"
            >
              <Send className="h-5 w-5" />
              {slide.cta}
            </Link>

            {/* Stats */}
            <div className="mt-12 flex flex-wrap justify-center gap-8 text-white/90">
              <div>
                <div className="text-3xl font-bold">1000+</div>
                <div className="text-sm">Takipçi</div>
              </div>
              <div>
                <div className="text-3xl font-bold">500+</div>
                <div className="text-sm">Günlük Fırsat</div>
              </div>
              <div>
                <div className="text-3xl font-bold">%70</div>
                <div className="text-sm">Tasarruf Oranı</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Arrows */}
      <button
        onClick={prevSlide}
        className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white/30 text-white p-2 rounded-full backdrop-blur-sm transition-all"
        aria-label="Previous slide"
      >
        <ChevronLeft className="h-6 w-6" />
      </button>
      <button
        onClick={nextSlide}
        className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white/30 text-white p-2 rounded-full backdrop-blur-sm transition-all"
        aria-label="Next slide"
      >
        <ChevronRight className="h-6 w-6" />
      </button>

      {/* Indicators */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2">
        {slides.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentSlide(index)}
            className={`h-2 rounded-full transition-all ${
              index === currentSlide ? 'w-8 bg-white' : 'w-2 bg-white/50'
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </div>
  )
}
