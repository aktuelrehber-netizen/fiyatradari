'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { catalogProductsAPI, categoriesAPI } from '@/utils/api-client'
import { Plus, Search, Edit2, Trash2, Package, ExternalLink, Loader2 } from 'lucide-react'

interface CatalogProduct {
  id: number
  title: string
  slug: string
  brand?: string
  category_id: number
  category_name?: string
  description?: string
  meta_title?: string
  meta_description?: string
  seller_products_count: number
  min_price?: number
  created_at: string
  updated_at: string
}

interface Category {
  id: number
  name: string
}

export default function CatalogProductsPage() {
  const [catalogProducts, setCatalogProducts] = useState<CatalogProduct[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  
  // Pagination
  const [skip, setSkip] = useState(0)
  const [limit] = useState(50)
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [brandFilter, setBrandFilter] = useState('')
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<CatalogProduct | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    slug: '',
    description: '',
    category_id: 0,
    brand: '',
    meta_title: '',
    meta_description: ''
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadCatalogProducts()
    loadCategories()
  }, [skip, selectedCategory, brandFilter])

  const loadCategories = async () => {
    try {
      const data = await categoriesAPI.list()
      setCategories(data)
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }

  const loadCatalogProducts = async () => {
    setLoading(true)
    try {
      const params: any = { skip, limit }
      
      if (selectedCategory !== 'all') {
        params.category_id = parseInt(selectedCategory)
      }
      
      if (brandFilter) {
        params.brand = brandFilter
      }
      
      if (searchTerm) {
        params.search = searchTerm
      }
      
      const data = await catalogProductsAPI.list(params)
      setCatalogProducts(data.items || [])
      setTotalCount(data.total || 0)
    } catch (error) {
      console.error('Failed to load catalog products:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setSkip(0)
    loadCatalogProducts()
  }

  const handleOpenModal = (product?: CatalogProduct) => {
    if (product) {
      // Edit mode
      setEditingProduct(product)
      setFormData({
        title: product.title,
        slug: product.slug,
        description: product.description || '',
        category_id: product.category_id,
        brand: product.brand || '',
        meta_title: product.meta_title || '',
        meta_description: product.meta_description || ''
      })
    } else {
      // Create mode
      setEditingProduct(null)
      setFormData({
        title: '',
        slug: '',
        description: '',
        category_id: 0,
        brand: '',
        meta_title: '',
        meta_description: ''
      })
    }
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setEditingProduct(null)
    setFormData({
      title: '',
      slug: '',
      description: '',
      category_id: 0,
      brand: '',
      meta_title: '',
      meta_description: ''
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)

    try {
      if (editingProduct) {
        // Update
        await catalogProductsAPI.update(editingProduct.id, formData)
      } else {
        // Create
        await catalogProductsAPI.create(formData)
      }
      
      handleCloseModal()
      loadCatalogProducts()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'İşlem başarısız')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Bu katalog ürününü silmek istediğinizden emin misiniz? İlişkili satıcı ürünleri koparılacak.')) {
      return
    }

    try {
      await catalogProductsAPI.delete(id)
      loadCatalogProducts()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Silme işlemi başarısız')
    }
  }

  const handleNextPage = () => {
    if (skip + limit < totalCount) {
      setSkip(skip + limit)
    }
  }

  const handlePrevPage = () => {
    if (skip > 0) {
      setSkip(Math.max(0, skip - limit))
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Katalog Ürünleri</h1>
          <p className="text-muted-foreground mt-2">
            SEO optimize edilmiş katalog ürünlerini yönetin
          </p>
        </div>
        <Button onClick={() => handleOpenModal()}>
          <Plus className="h-4 w-4 mr-2" />
          Yeni Katalog Ürünü
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filtreler</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Arama</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Başlık, slug veya marka..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button onClick={handleSearch} size="sm">
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Kategori</Label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tümü</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id.toString()}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Marka</Label>
              <Input
                placeholder="Marka filtresi..."
                value={brandFilter}
                onChange={(e) => setBrandFilter(e.target.value)}
              />
            </div>
            
            <div className="flex items-end">
              <Button 
                variant="outline" 
                onClick={() => {
                  setSearchTerm('')
                  setSelectedCategory('all')
                  setBrandFilter('')
                  setSkip(0)
                }}
              >
                Filtreleri Temizle
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Katalog Ürünleri ({totalCount})</CardTitle>
          <CardDescription>
            Toplam {totalCount} katalog ürünü bulundu
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Başlık</TableHead>
                    <TableHead>Slug</TableHead>
                    <TableHead>Marka</TableHead>
                    <TableHead>Kategori</TableHead>
                    <TableHead>Satıcı Ürün</TableHead>
                    <TableHead>Min Fiyat</TableHead>
                    <TableHead className="text-right">İşlemler</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {catalogProducts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                        Katalog ürünü bulunamadı
                      </TableCell>
                    </TableRow>
                  ) : (
                    catalogProducts.map((product) => (
                      <TableRow key={product.id}>
                        <TableCell className="font-medium">{product.id}</TableCell>
                        <TableCell className="max-w-xs truncate">{product.title}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">{product.slug}</TableCell>
                        <TableCell>{product.brand || '-'}</TableCell>
                        <TableCell>{product.category_name || '-'}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Package className="h-4 w-4" />
                            {product.seller_products_count}
                          </div>
                        </TableCell>
                        <TableCell>
                          {product.min_price ? `${product.min_price.toFixed(2)} ₺` : '-'}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleOpenModal(product)}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(product.id)}
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-muted-foreground">
                  {skip + 1} - {Math.min(skip + limit, totalCount)} / {totalCount}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handlePrevPage}
                    disabled={skip === 0}
                  >
                    Önceki
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleNextPage}
                    disabled={skip + limit >= totalCount}
                  >
                    Sonraki
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingProduct ? 'Katalog Ürünü Düzenle' : 'Yeni Katalog Ürünü'}
            </DialogTitle>
            <DialogDescription>
              {editingProduct ? 'Katalog ürün bilgilerini güncelleyin' : 'Yeni bir katalog ürünü oluşturun'}
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Başlık *</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="SEO optimize edilmiş ürün başlığı"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="slug">Slug</Label>
              <Input
                id="slug"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                placeholder="otomatik oluşturulur (opsiyonel)"
              />
              <p className="text-xs text-muted-foreground">
                Boş bırakılırsa başlıktan otomatik oluşturulur
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="category">Kategori *</Label>
              <Select
                value={formData.category_id.toString()}
                onValueChange={(value) => setFormData({ ...formData, category_id: parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Kategori seçin" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id.toString()}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="brand">Marka</Label>
              <Input
                id="brand"
                value={formData.brand}
                onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                placeholder="Ürün markası"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Açıklama</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Ürün açıklaması"
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="meta_title">Meta Title (SEO)</Label>
              <Input
                id="meta_title"
                value={formData.meta_title}
                onChange={(e) => setFormData({ ...formData, meta_title: e.target.value })}
                placeholder="SEO başlığı"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="meta_description">Meta Description (SEO)</Label>
              <Textarea
                id="meta_description"
                value={formData.meta_description}
                onChange={(e) => setFormData({ ...formData, meta_description: e.target.value })}
                placeholder="SEO açıklaması (max 160 karakter)"
                rows={2}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCloseModal}>
                İptal
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Kaydediliyor...
                  </>
                ) : (
                  editingProduct ? 'Güncelle' : 'Oluştur'
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
