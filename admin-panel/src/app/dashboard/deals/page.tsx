'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command'
import { dealsAPI, categoriesAPI } from '@/utils/api-client'
import { formatTurkishPrice } from '@/utils/format'
import { Eye, Send, CheckCircle, XCircle, Edit, RefreshCw, Filter, ExternalLink, Search, Check, ChevronsUpDown, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { PaginationControls } from '@/components/pagination-controls'
import { useToast } from '@/hooks/use-toast'
import { DealViewModal } from '@/components/modals/deal-view-modal'
import Image from 'next/image'

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
  product: {
    image_url: string | null
    detail_page_url: string | null
    brand: string | null
    asin: string | null
    rating: number | null
    review_count: number | null
    category_id: number | null
  } | null
}

interface Category {
  id: number
  name: string
  amazon_node_id: string
}

export default function DealsPage() {
  const { toast } = useToast()
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'active' | 'published' | 'telegram_sent'>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [categories, setCategories] = useState<Category[]>([])
  const [categoryOpen, setCategoryOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const [perPage] = useState(50)
  const [viewModalOpen, setViewModalOpen] = useState(false)
  const [selectedDealId, setSelectedDealId] = useState<number | null>(null)

  const AMAZON_PARTNER_TAG = 'firsatradar06-21'

  useEffect(() => {
    loadCategories()
  }, [])

  useEffect(() => {
    setCurrentPage(1)
    loadDeals(1)
  }, [filter, categoryFilter])

  const loadCategories = async () => {
    try {
      const data = await categoriesAPI.list()
      setCategories(data)
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }

  const loadDeals = async (page: number = 1) => {
    setLoading(true)
    try {
      const params: any = {
        skip: (page - 1) * perPage,
        limit: perPage,
      }
      
      if (search.trim()) {
        params.search = search.trim()
      }
      
      if (filter === 'active') {
        params.is_active = true
      } else if (filter === 'published') {
        params.is_published = true
      } else if (filter === 'telegram_sent') {
        params.telegram_sent = true
      }
      
      if (categoryFilter !== 'all') {
        params.category_id = parseInt(categoryFilter)
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

  const handleSearch = () => {
    setCurrentPage(1)
    loadDeals(1)
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

      <Card>
        <CardHeader>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="flex-1 flex gap-2">
                <Input
                  placeholder="Fırsat adı ile ara..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="flex-1"
                />
                <Button onClick={handleSearch}>
                  <Search className="h-4 w-4 mr-2" />
                  Ara
                </Button>
              </div>
            </div>
            
            <div className="flex items-center gap-2 flex-wrap">
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
                variant={filter === 'published' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('published')}
              >
                Yayındakiler
              </Button>
              <Button
                variant={filter === 'telegram_sent' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('telegram_sent')}
              >
                Telegram'a Gönderilenler
              </Button>
              
              <Popover open={categoryOpen} onOpenChange={setCategoryOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={categoryOpen}
                    size="sm"
                    className="w-[180px] justify-between"
                  >
                    {categoryFilter === 'all'
                      ? 'Kategori Seç...'
                      : categories.find((cat) => cat.id.toString() === categoryFilter)?.name || 'Kategori Seç...'}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[180px] p-0">
                  <Command>
                    <CommandInput placeholder="Kategori ara..." />
                    <CommandList>
                      <CommandEmpty>Kategori bulunamadı.</CommandEmpty>
                      <CommandGroup>
                        <CommandItem
                          value="all"
                          onSelect={() => {
                            setCategoryFilter('all')
                            setCategoryOpen(false)
                          }}
                        >
                          <Check
                            className={cn(
                              'mr-2 h-4 w-4',
                              categoryFilter === 'all' ? 'opacity-100' : 'opacity-0'
                            )}
                          />
                          Tüm Kategoriler
                        </CommandItem>
                        {categories.map((cat) => (
                          <CommandItem
                            key={cat.id}
                            value={cat.name}
                            onSelect={() => {
                              setCategoryFilter(cat.id.toString())
                              setCategoryOpen(false)
                            }}
                          >
                            <Check
                              className={cn(
                                'mr-2 h-4 w-4',
                                categoryFilter === cat.id.toString() ? 'opacity-100' : 'opacity-0'
                              )}
                            />
                            {cat.name}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
              
              {(filter !== 'all' || categoryFilter !== 'all' || search.trim()) && (
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => {
                    setFilter('all')
                    setCategoryFilter('all')
                    setSearch('')
                    setCurrentPage(1)
                    loadDeals(1)
                  }}
                >
                  <X className="h-4 w-4 mr-1" />
                  Temizle
                </Button>
              )}
              
              {totalItems > 0 && (
                <Badge variant="secondary" className="ml-auto">
                  {totalItems}+ Fırsat
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Fırsat Listesi</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-16">Resim</TableHead>
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
                  <TableCell colSpan={8} className="text-center text-gray-500 py-8">
                    {search ? 'Fırsat bulunamadı' : 'Henüz fırsat tespit edilmemiş'}
                  </TableCell>
                </TableRow>
              ) : (
                deals.map((deal) => (
                  <TableRow key={deal.id}>
                    <TableCell className="py-2">
                      {deal.product?.image_url && (
                        <div className="relative h-12 w-12 bg-gray-100 rounded">
                          <Image
                            src={deal.product.image_url}
                            alt={deal.title}
                            fill
                            sizes="48px"
                            className="object-contain p-1"
                          />
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium line-clamp-2">{deal.title}</div>
                      {deal.product?.brand && (
                        <div className="text-xs text-gray-500 mt-0.5">{deal.product.brand}</div>
                      )}
                      {deal.product?.rating && (
                        <div className="text-xs text-gray-500 mt-0.5">
                          ⭐ {deal.product.rating}/5 ({deal.product.review_count} değerlendirme)
                        </div>
                      )}
                      <div className="text-xs text-gray-400 mt-1">
                        {new Date(deal.created_at).toLocaleDateString('tr-TR')}
                      </div>
                    </TableCell>
                    <TableCell className="text-right text-gray-500 line-through">
                      {formatTurkishPrice(parseFloat(deal.original_price))} ₺
                    </TableCell>
                    <TableCell className="text-right font-semibold text-green-600">
                      {formatTurkishPrice(parseFloat(deal.deal_price))} ₺
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
                        {deal.product?.detail_page_url && (
                          <a 
                            href={deal.product.detail_page_url || `https://www.amazon.com.tr/dp/${deal.product.asin}?tag=${AMAZON_PARTNER_TAG}`}
                            target="_blank" 
                            rel="noopener noreferrer"
                            title="Amazon'da Görüntüle"
                          >
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          </a>
                        )}
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
