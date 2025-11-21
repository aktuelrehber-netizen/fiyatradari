'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Trash2, RefreshCw, CheckCircle, XCircle, Info } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface CacheStats {
  available: boolean
  backend?: string
  ttl?: {
    deals: string
    products: string
    categories: string
  }
  message?: string
}

export function CacheManager() {
  const [clearing, setClearing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const loadStats = async () => {
    setLoading(true)
    setMessage(null)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/api/v1/cache/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Cache istatistikleri alınamadı')
      }

      const data = await response.json()
      setStats(data)
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.message || 'Bir hata oluştu'
      })
    } finally {
      setLoading(false)
    }
  }

  const clearCache = async () => {
    if (!confirm('Tüm cache temizlenecek. Emin misiniz?')) {
      return
    }

    setClearing(true)
    setMessage(null)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`${API_URL}/api/v1/cache/clear`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Cache temizlenemedi')
      }

      const data = await response.json()
      setMessage({
        type: 'success',
        text: data.message || 'Cache başarıyla temizlendi'
      })

      // Reload stats after clearing
      setTimeout(() => loadStats(), 500)
    } catch (err: any) {
      setMessage({
        type: 'error',
        text: err.message || 'Bir hata oluştu'
      })
    } finally {
      setClearing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <RefreshCw className="h-5 w-5" />
          Cache Yönetimi
        </CardTitle>
        <CardDescription>
          Backend cache durumunu görüntüle ve temizle
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Actions */}
        <div className="flex gap-2">
          <Button
            onClick={loadStats}
            disabled={loading}
            variant="outline"
            size="sm"
          >
            <Info className="h-4 w-4 mr-2" />
            {loading ? 'Yükleniyor...' : 'İstatistikleri Göster'}
          </Button>
          <Button
            onClick={clearCache}
            disabled={clearing}
            variant="destructive"
            size="sm"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            {clearing ? 'Temizleniyor...' : 'Cache Temizle'}
          </Button>
        </div>

        {/* Message */}
        {message && (
          <div className={`flex items-center gap-2 p-3 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-700 border border-green-200' 
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            <span className="text-sm font-medium">{message.text}</span>
          </div>
        )}

        {/* Stats */}
        {stats && (
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Durum</span>
              <Badge variant={stats.available ? "default" : "secondary"}>
                {stats.available ? '✓ Aktif' : '✗ Devre Dışı'}
              </Badge>
            </div>

            {stats.available && stats.backend && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Backend</span>
                <Badge variant="outline">{stats.backend}</Badge>
              </div>
            )}

            {stats.available && stats.ttl && (
              <div className="space-y-2 pt-2 border-t">
                <div className="text-sm font-semibold text-gray-800 mb-2">Cache TTL Ayarları</div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Deals</span>
                  <Badge variant="secondary" className="font-mono text-xs">
                    {stats.ttl.deals}
                  </Badge>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Products</span>
                  <Badge variant="secondary" className="font-mono text-xs">
                    {stats.ttl.products}
                  </Badge>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Categories</span>
                  <Badge variant="secondary" className="font-mono text-xs">
                    {stats.ttl.categories}
                  </Badge>
                </div>
              </div>
            )}

            {!stats.available && stats.message && (
              <div className="text-sm text-gray-500 italic">
                {stats.message}
              </div>
            )}
          </div>
        )}

        {/* Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700">
          <strong>Not:</strong> Cache otomatik olarak belirtilen sürelerde yenilenir. 
          Manuel temizleme sadece acil güncellemeler için kullanılmalıdır.
        </div>
      </CardContent>
    </Card>
  )
}
