'use client'

import { useEffect, useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { productsAPI } from '@/utils/api-client'
import { useToast } from '@/hooks/use-toast'
import { ExternalLink, TrendingDown, TrendingUp, Calendar, DollarSign } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import Image from 'next/image'

interface Product {
  id: number
  asin: string
  title: string
  brand: string
  current_price: string
  list_price: string
  currency: string
  image_url: string
  detail_page_url: string
  is_active: boolean
  is_available: boolean
  rating: number
  review_count: number
  last_checked_at: string
  created_at: string
  updated_at: string
}

interface PriceHistory {
  id: number
  product_id: number
  price: string
  list_price: string | null
  currency: string
  is_available: boolean
  recorded_at: string
}

interface ProductViewModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  productId: number | null
  onSuccess?: () => void
}

export function ProductViewModal({ open, onOpenChange, productId, onSuccess }: ProductViewModalProps) {
  const { toast } = useToast()
  const [product, setProduct] = useState<Product | null>(null)
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([])
  const [loading, setLoading] = useState(false)
  const [toggling, setToggling] = useState(false)

  useEffect(() => {
    if (open && productId) {
      loadProduct()
      loadPriceHistory()
    }
  }, [open, productId])

  const loadProduct = async () => {
    if (!productId) return
    
    setLoading(true)
    try {
      const data = await productsAPI.get(productId)
      setProduct(data)
    } catch (error) {
      console.error('Ürün yüklenemedi:', error)
      toast({
        title: 'Hata',
        description: 'Ürün bilgileri yüklenemedi',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const loadPriceHistory = async () => {
    if (!productId) return
    
    try {
      const data = await productsAPI.getPriceHistory(productId, 30)
      setPriceHistory(data)
    } catch (error) {
      console.error('Fiyat geçmişi yüklenemedi:', error)
    }
  }

  const handleToggleActive = async () => {
    if (!product) return
    
    setToggling(true)
    try {
      await productsAPI.update(product.id, { is_active: !product.is_active })
      toast({
        title: 'Başarılı',
        description: `Ürün ${!product.is_active ? 'aktif' : 'pasif'} edildi`,
      })
      setProduct({ ...product, is_active: !product.is_active })
      onSuccess?.()
    } catch (error: any) {
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'İşlem başarısız oldu',
        variant: 'destructive',
      })
    } finally {
      setToggling(false)
    }
  }

  const handleDelete = async () => {
    if (!product || !confirm('Bu ürünü silmek istediğinizden emin misiniz?')) return
    
    try {
      await productsAPI.delete(product.id)
      toast({
        title: 'Başarılı',
        description: 'Ürün silindi',
      })
      onOpenChange(false)
      onSuccess?.()
    } catch (error: any) {
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'Silme işlemi başarısız oldu',
        variant: 'destructive',
      })
    }
  }

  if (loading || !product) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl">
          <div className="text-center py-12">Yükleniyor...</div>
        </DialogContent>
      </Dialog>
    )
  }

  // Chart data preparation
  const chartData = priceHistory.map(item => ({
    date: new Date(item.recorded_at).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' }),
    price: parseFloat(item.price),
    list_price: item.list_price ? parseFloat(item.list_price) : null
  }))

  const currentPrice = parseFloat(product.current_price)
  const listPrice = product.list_price ? parseFloat(product.list_price) : null
  const hasDiscount = listPrice && listPrice > currentPrice
  const discountPercentage = hasDiscount ? ((listPrice - currentPrice) / listPrice * 100) : 0

  // Calculate price trend
  const priceChange = priceHistory.length >= 2 
    ? parseFloat(priceHistory[priceHistory.length - 1].price) - parseFloat(priceHistory[0].price)
    : 0
  const priceChangePercent = priceHistory.length >= 2 
    ? (priceChange / parseFloat(priceHistory[0].price)) * 100
    : 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Ürün Detayları
            <Badge variant={product.is_active ? 'success' : 'secondary'}>
              {product.is_active ? 'Aktif' : 'Pasif'}
            </Badge>
            {!product.is_available && (
              <Badge variant="destructive">Stokta Yok</Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            ASIN: {product.asin}
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-3 gap-6">
          {/* Left: Image & Basic Info */}
          <div className="space-y-4">
            {product.image_url && (
              <div className="relative h-64 w-full bg-gray-100 rounded-lg">
                <Image
                  src={product.image_url}
                  alt={product.title}
                  fill
                  sizes="(max-width: 768px) 100vw, 33vw"
                  className="object-contain p-4"
                />
              </div>
            )}
            
            <div className="space-y-2">
              <div>
                <Label className="text-xs text-gray-500">Marka</Label>
                <p className="font-medium">{product.brand || '-'}</p>
              </div>
              
              {product.rating && (
                <div>
                  <Label className="text-xs text-gray-500">Değerlendirme</Label>
                  <p className="font-medium">
                    ⭐ {product.rating}/5 ({product.review_count} yorum)
                  </p>
                </div>
              )}
              
              <div>
                <Label className="text-xs text-gray-500">Son Kontrol</Label>
                <p className="text-sm">
                  {new Date(product.last_checked_at).toLocaleString('tr-TR')}
                </p>
              </div>
              
              {product.detail_page_url && (
                <a
                  href={product.detail_page_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-blue-600 hover:underline"
                >
                  <ExternalLink className="h-4 w-4" />
                  Amazon'da Görüntüle
                </a>
              )}
            </div>
          </div>

          {/* Middle & Right: Details & Chart */}
          <div className="col-span-2 space-y-4">
            <div>
              <h3 className="font-semibold text-lg line-clamp-2">{product.title}</h3>
            </div>

            {/* Price Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                  <DollarSign className="h-4 w-4" />
                  Güncel Fiyat
                </div>
                <div className="text-2xl font-bold">
                  {currentPrice.toFixed(2)} {product.currency}
                </div>
                {hasDiscount && (
                  <div className="mt-2">
                    <div className="text-sm text-gray-500 line-through">
                      {listPrice!.toFixed(2)} {product.currency}
                    </div>
                    <Badge variant="success" className="mt-1">
                      %{discountPercentage.toFixed(0)} İndirim
                    </Badge>
                  </div>
                )}
              </div>

              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                  <Calendar className="h-4 w-4" />
                  30 Günlük Trend
                </div>
                <div className="flex items-center gap-2">
                  {priceChangePercent > 0 ? (
                    <TrendingUp className="h-6 w-6 text-red-600" />
                  ) : priceChangePercent < 0 ? (
                    <TrendingDown className="h-6 w-6 text-green-600" />
                  ) : (
                    <span className="h-6 w-6" />
                  )}
                  <span className={`text-2xl font-bold ${
                    priceChangePercent > 0 ? 'text-red-600' : 
                    priceChangePercent < 0 ? 'text-green-600' : 
                    'text-gray-600'
                  }`}>
                    {priceChangePercent > 0 ? '+' : ''}{priceChangePercent.toFixed(1)}%
                  </span>
                </div>
                <div className="text-sm text-gray-500 mt-2">
                  {priceChange > 0 ? '+' : ''}{priceChange.toFixed(2)} {product.currency}
                </div>
              </div>
            </div>

            {/* Price Chart */}
            <div className="p-4 bg-white border rounded-lg">
              <h4 className="font-semibold mb-4">Fiyat Geçmişi (Son 30 Gün)</h4>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="price" 
                      stroke="#3b82f6" 
                      strokeWidth={2} 
                      name="Fiyat"
                      dot={{ r: 3 }}
                    />
                    {chartData.some(d => d.list_price) && (
                      <Line 
                        type="monotone" 
                        dataKey="list_price" 
                        stroke="#94a3b8" 
                        strokeWidth={1} 
                        strokeDasharray="5 5"
                        name="Liste Fiyatı"
                        dot={false}
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-gray-500 text-center py-8">
                  Henüz fiyat geçmişi yok
                </p>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Switch
                  checked={product.is_active}
                  onCheckedChange={handleToggleActive}
                  disabled={toggling}
                />
                <div>
                  <Label className="cursor-pointer">Takip Durumu</Label>
                  <p className="text-xs text-gray-500">
                    {product.is_active ? 'Fiyat takibi aktif' : 'Fiyat takibi durduruldu'}
                  </p>
                </div>
              </div>
              
              <Button
                variant="destructive"
                onClick={handleDelete}
                size="sm"
              >
                Ürünü Sil
              </Button>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Kapat
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
