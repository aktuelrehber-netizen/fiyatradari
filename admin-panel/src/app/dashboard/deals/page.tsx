'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { dealsAPI } from '@/utils/api-client'
import { Eye, Send, CheckCircle, XCircle, Edit, RefreshCw, Filter } from 'lucide-react'
import { PaginationControls } from '@/components/pagination-controls'
import { useToast } from '@/hooks/use-toast'
import { DealViewModal } from '@/components/modals/deal-view-modal'

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

export default function DealsPage() {
  const { toast } = useToast()
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'active' | 'published' | 'pending'>('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const [perPage] = useState(50)
  const [viewModalOpen, setViewModalOpen] = useState(false)
  const [selectedDealId, setSelectedDealId] = useState<number | null>(null)

  useEffect(() => {
    setCurrentPage(1)
    loadDeals(1)
  }, [filter])

  const loadDeals = async (page: number = 1) => {
    setLoading(true)
    try {
      const params: any = {
        skip: (page - 1) * perPage,
        limit: perPage,
      }
      
      if (filter === 'active') {
        params.is_active = true
      } else if (filter === 'published') {
        params.is_published = true
      } else if (filter === 'pending') {
        params.is_published = false
        params.is_active = true
      }
      
      const data = await dealsAPI.list(params)
      setDeals(data.items || data)
      setTotalItems(data.total || data.length)
    } catch (error) {
      toast({
        title: 'Hata',
        description: 'Fırsatlar yüklenirken hata oluştu',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handlePublish = async (id: number) => {
    // Optimistic update - UI'ı hemen güncelle
    setDeals(prev => prev.map(deal => 
      deal.id === id 
        ? { ...deal, is_published: true, published_at: new Date().toISOString() }
        : deal
    ))

    try {
      await dealsAPI.publish(id)
      toast({
        title: 'Başarılı',
        description: 'Fırsat yayınlandı',
        variant: 'success',
      })
    } catch (error: any) {
      // Rollback - başarısız olursa geri al
      setDeals(prev => prev.map(deal => 
        deal.id === id 
          ? { ...deal, is_published: false, published_at: null }
          : deal
      ))
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'Yayınlama başarısız oldu',
        variant: 'destructive',
      })
    }
  }

  const handleUnpublish = async (id: number) => {
    // Optimistic update - UI'ı hemen güncelle
    setDeals(prev => prev.map(deal => 
      deal.id === id 
        ? { ...deal, is_published: false, published_at: null }
        : deal
    ))

    try {
      await dealsAPI.unpublish(id)
      toast({
        title: 'Başarılı',
        description: 'Fırsat yayından kaldırıldı',
        variant: 'success',
      })
    } catch (error: any) {
      // Rollback - başarısız olursa geri al
      const originalDeal = deals.find(d => d.id === id)
      if (originalDeal?.published_at) {
        setDeals(prev => prev.map(deal => 
          deal.id === id 
            ? { ...deal, is_published: true, published_at: originalDeal.published_at }
            : deal
        ))
      }
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'Yayından kaldırma başarısız oldu',
        variant: 'destructive',
      })
    }
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    loadDeals(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  if (loading) {
    return <div className="text-center py-12">Yükleniyor...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Fırsatlar & İndirimler</h1>
          <p className="text-gray-500 mt-1">
            Tespit edilen fırsatları görüntüleyin, yönetin ve Telegram'da yayınlayın
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => loadDeals(currentPage)}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Yenile
        </Button>
      </div>

      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-gray-500" />
        <Button
          variant={filter === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('all')}
        >
          Tümü
        </Button>
        <Button
          variant={filter === 'active' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('active')}
        >
          Aktif
        </Button>
        <Button
          variant={filter === 'pending' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('pending')}
        >
          Onay Bekleyenler
        </Button>
        <Button
          variant={filter === 'published' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('published')}
        >
          Yayınlananlar
        </Button>
        {totalItems > 0 && (
          <Badge variant="secondary" className="ml-auto">
            {totalItems}+ Fırsat
          </Badge>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Fırsat Listesi</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Fırsat Başlığı</TableHead>
                <TableHead className="text-right">Orijinal Fiyat</TableHead>
                <TableHead className="text-right">İndirimli Fiyat</TableHead>
                <TableHead className="text-center">İndirim</TableHead>
                <TableHead className="text-center">Durum</TableHead>
                <TableHead className="text-center">Telegram</TableHead>
                <TableHead className="text-right">İşlemler</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {deals.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-gray-500 py-8">
                    Henüz fırsat tespit edilmemiş
                  </TableCell>
                </TableRow>
              ) : (
                deals.map((deal) => (
                  <TableRow key={deal.id}>
                    <TableCell>
                      <div className="font-medium">{deal.title}</div>
                      {deal.description && (
                        <div className="text-sm text-gray-500 line-clamp-1 mt-1">
                          {deal.description}
                        </div>
                      )}
                      <div className="text-xs text-gray-400 mt-1">
                        {new Date(deal.created_at).toLocaleDateString('tr-TR')}
                      </div>
                    </TableCell>
                    <TableCell className="text-right text-gray-500 line-through">
                      {parseFloat(deal.original_price).toFixed(2)} {deal.currency}
                    </TableCell>
                    <TableCell className="text-right font-semibold text-green-600">
                      {parseFloat(deal.deal_price).toFixed(2)} {deal.currency}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="warning" className="font-bold">
                        %{deal.discount_percentage.toFixed(0)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex flex-col items-center gap-1">
                        <Badge variant={deal.is_active ? 'success' : 'secondary'}>
                          {deal.is_active ? 'Aktif' : 'Pasif'}
                        </Badge>
                        {deal.is_published && (
                          <Badge variant="info">Yayında</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      {deal.telegram_sent ? (
                        <div className="flex flex-col items-center gap-1">
                          <CheckCircle className="h-5 w-5 text-green-600" />
                          <div className="text-xs text-gray-500">
                            {deal.telegram_sent_at && new Date(deal.telegram_sent_at).toLocaleString('tr-TR')}
                          </div>
                        </div>
                      ) : (
                        <XCircle className="h-5 w-5 text-gray-400 mx-auto" />
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => {
                            setSelectedDealId(deal.id)
                            setViewModalOpen(true)
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {!deal.is_published ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handlePublish(deal.id)}
                          >
                            <Send className="h-4 w-4 text-blue-500" />
                          </Button>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleUnpublish(deal.id)}
                          >
                            <XCircle className="h-4 w-4 text-red-500" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <PaginationControls
        currentPage={currentPage}
        totalPages={Math.ceil(totalItems / perPage)}
        onPageChange={handlePageChange}
      />

      <DealViewModal
        open={viewModalOpen}
        onOpenChange={setViewModalOpen}
        dealId={selectedDealId}
        onSuccess={() => loadDeals(currentPage)}
      />
    </div>
  )
}
