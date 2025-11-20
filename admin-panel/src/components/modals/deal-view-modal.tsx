'use client'

import { useEffect, useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { dealsAPI } from '@/utils/api-client'
import { useToast } from '@/hooks/use-toast'
import { Send, CheckCircle, XCircle, TrendingDown, Calendar, DollarSign } from 'lucide-react'

interface Deal {
  id: number
  product_id: number
  title: string
  description: string
  original_price: string
  deal_price: string
  discount_amount: string
  discount_percentage: number
  currency: string
  is_active: boolean
  is_published: boolean
  telegram_sent: boolean
  telegram_sent_at: string | null
  published_at: string | null
  created_at: string
}

interface DealViewModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  dealId: number | null
  onSuccess?: () => void
}

export function DealViewModal({ open, onOpenChange, dealId, onSuccess }: DealViewModalProps) {
  const { toast } = useToast()
  const [deal, setDeal] = useState<Deal | null>(null)
  const [loading, setLoading] = useState(false)
  const [publishing, setPublishing] = useState(false)

  useEffect(() => {
    if (open && dealId) {
      loadDeal()
    }
  }, [open, dealId])

  const loadDeal = async () => {
    if (!dealId) return
    
    setLoading(true)
    try {
      const data = await dealsAPI.get(dealId)
      setDeal(data)
    } catch (error) {
      console.error('Fırsat yüklenemedi:', error)
      toast({
        title: 'Hata',
        description: 'Fırsat bilgileri yüklenemedi',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handlePublish = async () => {
    if (!deal) return
    
    setPublishing(true)
    try {
      if (deal.is_published) {
        await dealsAPI.unpublish(deal.id)
        toast({
          title: 'Başarılı',
          description: 'Fırsat yayından kaldırıldı',
        })
        setDeal({ ...deal, is_published: false })
      } else {
        await dealsAPI.publish(deal.id)
        toast({
          title: 'Başarılı',
          description: 'Fırsat yayınlandı',
        })
        setDeal({ ...deal, is_published: true })
      }
      onSuccess?.()
    } catch (error: any) {
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'İşlem başarısız oldu',
        variant: 'destructive',
      })
    } finally {
      setPublishing(false)
    }
  }

  const handleDelete = async () => {
    if (!deal || !confirm('Bu fırsatı silmek istediğinizden emin misiniz?')) return
    
    try {
      await dealsAPI.delete(deal.id)
      toast({
        title: 'Başarılı',
        description: 'Fırsat silindi',
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

  if (loading || !deal) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl">
          <div className="text-center py-12">Yükleniyor...</div>
        </DialogContent>
      </Dialog>
    )
  }

  const originalPrice = parseFloat(deal.original_price)
  const dealPrice = parseFloat(deal.deal_price)
  const savings = originalPrice - dealPrice

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Fırsat Detayları
            <Badge variant={deal.is_active ? 'success' : 'secondary'}>
              {deal.is_active ? 'Aktif' : 'Pasif'}
            </Badge>
            {deal.is_published && (
              <Badge variant="info">Yayında</Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            {new Date(deal.created_at).toLocaleDateString('tr-TR', { 
              day: 'numeric', 
              month: 'long', 
              year: 'numeric' 
            })} tarihinde tespit edildi
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Title & Description */}
          <div>
            <h3 className="font-semibold text-xl mb-2">{deal.title}</h3>
            {deal.description && (
              <p className="text-gray-600">{deal.description}</p>
            )}
          </div>

          {/* Price Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg border">
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                <DollarSign className="h-4 w-4" />
                Orijinal Fiyat
              </div>
              <div className="text-2xl font-bold text-gray-400 line-through">
                {originalPrice.toFixed(2)} {deal.currency}
              </div>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 text-sm text-green-700 mb-2">
                <TrendingDown className="h-4 w-4" />
                Fırsat Fiyatı
              </div>
              <div className="text-2xl font-bold text-green-600">
                {dealPrice.toFixed(2)} {deal.currency}
              </div>
            </div>

            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <div className="text-sm text-orange-700 mb-2">
                İndirim Oranı
              </div>
              <div className="text-3xl font-bold text-orange-600">
                %{deal.discount_percentage.toFixed(0)}
              </div>
              <div className="text-sm text-orange-600 mt-1">
                {savings.toFixed(2)} {deal.currency} tasarruf
              </div>
            </div>
          </div>

          {/* Telegram Status */}
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-blue-900">Telegram Durumu</Label>
                <div className="flex items-center gap-2 mt-2">
                  {deal.telegram_sent ? (
                    <>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span className="text-sm text-gray-700">
                        Mesaj gönderildi
                      </span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-5 w-5 text-gray-400" />
                      <span className="text-sm text-gray-500">
                        Henüz gönderilmedi
                      </span>
                    </>
                  )}
                </div>
                {deal.telegram_sent_at && (
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(deal.telegram_sent_at).toLocaleString('tr-TR')}
                  </p>
                )}
              </div>
              
              <Button
                onClick={handlePublish}
                disabled={publishing}
                variant={deal.is_published ? "outline" : "default"}
                className={deal.is_published ? "border-red-300 text-red-600 hover:bg-red-50" : ""}
              >
                {publishing ? (
                  'İşlem yapılıyor...'
                ) : deal.is_published ? (
                  <>
                    <XCircle className="h-4 w-4 mr-2" />
                    Yayından Kaldır
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Yayınla
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Timeline */}
          <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
            <Label className="text-gray-700">Zaman Çizelgesi</Label>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-400" />
                <span className="text-gray-600">Oluşturulma:</span>
                <span className="font-medium">
                  {new Date(deal.created_at).toLocaleString('tr-TR')}
                </span>
              </div>
              {deal.published_at && (
                <div className="flex items-center gap-2">
                  <Send className="h-4 w-4 text-blue-500" />
                  <span className="text-gray-600">Yayınlanma:</span>
                  <span className="font-medium">
                    {new Date(deal.published_at).toLocaleString('tr-TR')}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        <DialogFooter className="flex items-center justify-between">
          <Button
            variant="destructive"
            onClick={handleDelete}
            size="sm"
          >
            Fırsatı Sil
          </Button>
          
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Kapat
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
