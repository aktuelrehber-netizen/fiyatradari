'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { productsAPI } from '@/utils/api-client'
import { Search, Eye, Edit, Trash2, ExternalLink, RefreshCw, Filter, ToggleLeft, ToggleRight } from 'lucide-react'
import { PaginationControls } from '@/components/pagination-controls'
import { useToast } from '@/hooks/use-toast'
import { ProductViewModal } from '@/components/modals/product-view-modal'
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
}

export default function ProductsPage() {
  const { toast } = useToast()
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const [perPage, setPerPage] = useState(50)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [availabilityFilter, setAvailabilityFilter] = useState<string>('all')
  const [viewModalOpen, setViewModalOpen] = useState(false)
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null)

  useEffect(() => {
    loadProducts(currentPage)
  }, [statusFilter, availabilityFilter, perPage])

  const loadProducts = async (page: number = 1) => {
    setLoading(true)
    try {
      const params: any = {
        skip: (page - 1) * perPage,
        limit: perPage,
      }
      
      if (search.trim()) {
        params.search = search.trim()
      }
      
      if (statusFilter !== 'all') {
        params.is_active = statusFilter === 'active'
      }
      
      if (availabilityFilter !== 'all') {
        params.is_available = availabilityFilter === 'available'
      }
      
      const data = await productsAPI.list(params)
      setProducts(data.items || data)
      setTotalItems(data.total || data.length)
    } catch (error) {
      toast({
        title: 'Hata',
        description: 'Ürünler yüklenirken hata oluştu',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setCurrentPage(1)
    loadProducts(1)
  }
  
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    loadProducts(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  
  const handleFilterChange = () => {
    setCurrentPage(1)
    loadProducts(1)
  }

  const handleToggleActive = async (id: number) => {
    // Optimistic update - durumu hemen değiştir
    setProducts(prev => prev.map(product =>
      product.id === id
        ? { ...product, is_active: !product.is_active }
        : product
    ))

    try {
      await productsAPI.toggleActive(id)
      toast({
        title: 'Başarılı',
        description: 'Ürün durumu güncellendi',
        variant: 'success',
      })
    } catch (error: any) {
      // Rollback - başarısız olursa geri al
      setProducts(prev => prev.map(product =>
        product.id === id
          ? { ...product, is_active: !product.is_active }
          : product
      ))
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'Durum değiştirme başarısız oldu',
        variant: 'destructive',
      })
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Bu ürünü silmek istediğinizden emin misiniz?')) {
      return
    }

    // Optimistic update - UI'dan hemen kaldır
    const deletedProduct = products.find(p => p.id === id)
    setProducts(prev => prev.filter(product => product.id !== id))
    setTotalItems(prev => prev - 1)

    try {
      await productsAPI.delete(id)
      toast({
        title: 'Başarılı',
        description: 'Ürün silindi',
        variant: 'success',
      })
    } catch (error: any) {
      // Rollback - başarısız olursa geri ekle
      if (deletedProduct) {
        setProducts(prev => [...prev, deletedProduct])
        setTotalItems(prev => prev + 1)
      }
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'Silme işlemi başarısız oldu',
        variant: 'destructive',
      })
    }
  }

  if (loading) {
    return <div className="text-center py-12">Yükleniyor...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Ürünler</h1>
          <p className="text-gray-500 mt-1">
            Takip edilen Amazon ürünlerini görüntüleyin ve yönetin
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => loadProducts(currentPage)}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Yenile
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="flex-1 flex gap-2">
                <Input
                  placeholder="ASIN, ürün adı veya marka ile ara..."
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
            
            <div className="flex items-center gap-4">
              <Filter className="h-4 w-4 text-gray-500" />
              <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); handleFilterChange(); }}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Durum" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tümü</SelectItem>
                  <SelectItem value="active">Aktif</SelectItem>
                  <SelectItem value="inactive">Pasif</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={availabilityFilter} onValueChange={(v) => { setAvailabilityFilter(v); handleFilterChange(); }}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Stok" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tümü</SelectItem>
                  <SelectItem value="available">Stokta</SelectItem>
                  <SelectItem value="unavailable">Stokta Yok</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={perPage.toString()} onValueChange={(v) => setPerPage(parseInt(v))}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="25">25 / sayfa</SelectItem>
                  <SelectItem value="50">50 / sayfa</SelectItem>
                  <SelectItem value="100">100 / sayfa</SelectItem>
                  <SelectItem value="200">200 / sayfa</SelectItem>
                </SelectContent>
              </Select>
              
              {totalItems > 0 && (
                <Badge variant="secondary" className="ml-auto">
                  {totalItems}+ Ürün
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="h-10">
                <TableHead className="w-16 text-xs py-2">Resim</TableHead>
                <TableHead className="text-xs py-2">Ürün</TableHead>
                <TableHead className="text-xs py-2">ASIN</TableHead>
                <TableHead className="text-right text-xs py-2">Fiyat</TableHead>
                <TableHead className="text-center text-xs py-2">Durum</TableHead>
                <TableHead className="text-right text-xs py-2">İşlemler</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {products.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-gray-500 py-8">
                    {search ? 'Ürün bulunamadı' : 'Henüz ürün eklenmemiş'}
                  </TableCell>
                </TableRow>
              ) : (
                products.map((product) => (
                  <TableRow key={product.id} className="h-16">
                    <TableCell className="py-2">
                      {product.image_url && (
                        <div className="relative h-10 w-10 bg-gray-100 rounded">
                          <Image
                            src={product.image_url}
                            alt={product.title}
                            fill
                            sizes="40px"
                            className="object-contain p-1"
                          />
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="py-2">
                      <div>
                        <div className="text-xs font-medium line-clamp-2 leading-tight">{product.title}</div>
                        {product.brand && (
                          <div className="text-xs text-gray-500 mt-0.5">{product.brand}</div>
                        )}
                        {product.rating && (
                          <div className="text-xs text-gray-500 mt-0.5">
                            ⭐ {product.rating}/5 ({product.review_count} değerlendirme)
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs py-2">{product.asin}</TableCell>
                    <TableCell className="text-right py-2">
                      <div className="text-xs font-semibold whitespace-nowrap">
                        {parseFloat(product.current_price).toFixed(2)} {product.currency === 'TRY' ? '₺' : product.currency}
                      </div>
                      {product.list_price && parseFloat(product.list_price) > parseFloat(product.current_price) && (
                        <div className="text-xs text-gray-500 line-through whitespace-nowrap">
                          {parseFloat(product.list_price).toFixed(2)} {product.currency === 'TRY' ? '₺' : product.currency}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-center py-2">
                      <div className="flex flex-col items-center justify-center gap-0.5 min-w-[80px]">
                        <Badge variant={product.is_active ? 'success' : 'secondary'} className="text-[10px] py-0 h-4 px-2 whitespace-nowrap">
                          {product.is_active ? 'Aktif' : 'Pasif'}
                        </Badge>
                        {!product.is_available && (
                          <Badge variant="destructive" className="text-[10px] py-0 h-4 px-2 whitespace-nowrap">Stokta Yok</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right py-2">
                      <div className="flex items-center justify-end gap-1">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="h-8 w-8 p-0"
                          onClick={() => handleToggleActive(product.id)}
                          title={product.is_active ? 'Pasif yap' : 'Aktif yap'}
                        >
                          {product.is_active ? (
                            <ToggleRight className="h-3.5 w-3.5 text-green-600" />
                          ) : (
                            <ToggleLeft className="h-3.5 w-3.5 text-gray-400" />
                          )}
                        </Button>
                        {product.detail_page_url && (
                          <a href={product.detail_page_url} target="_blank" rel="noopener noreferrer">
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              <ExternalLink className="h-3.5 w-3.5" />
                            </Button>
                          </a>
                        )}
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="h-8 w-8 p-0"
                          onClick={() => {
                            setSelectedProductId(product.id)
                            setViewModalOpen(true)
                          }}
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          className="h-8 w-8 p-0"
                          onClick={() => handleDelete(product.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-red-500" />
                        </Button>
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

      <ProductViewModal
        open={viewModalOpen}
        onOpenChange={setViewModalOpen}
        productId={selectedProductId}
        onSuccess={() => loadProducts(currentPage)}
      />
    </div>
  )
}
