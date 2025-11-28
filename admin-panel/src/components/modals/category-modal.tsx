'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { categoriesAPI, amazonAPI } from '@/utils/api-client'
import { useToast } from '@/hooks/use-toast'
import { X, Plus, Search, Loader2 } from 'lucide-react'

interface SelectionRules {
  min_rating?: number
  max_rating?: number
  min_review_count?: number
  min_price?: number
  max_price?: number
  min_discount_percentage?: number
  include_keywords?: string[]
  exclude_keywords?: string[]
  only_prime?: boolean
  only_deals?: boolean
}

interface Category {
  id?: number
  name: string
  slug: string
  description: string
  amazon_browse_node_ids: string[]
  parent_id?: number | null
  is_active: boolean
  meta_title?: string
  meta_description?: string
  meta_keywords?: string
  display_order?: number
  selection_rules?: SelectionRules
  max_products?: number
  check_interval_hours?: number
}

interface CategoryModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  category?: Category | null
  onSuccess?: () => void
}

export function CategoryModal({ open, onOpenChange, category, onSuccess }: CategoryModalProps) {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [categories, setCategories] = useState<Category[]>([])
  const [formData, setFormData] = useState<Category>({
    name: '',
    slug: '',
    description: '',
    amazon_browse_node_ids: [],
    parent_id: null,
    is_active: true,
    meta_title: '',
    meta_description: '',
    meta_keywords: '',
    display_order: 0,
    selection_rules: {},
    max_products: 100,
    check_interval_hours: 6,
  })
  
  const [newNodeId, setNewNodeId] = useState('')
  const [newIncludeKeyword, setNewIncludeKeyword] = useState('')
  const [newExcludeKeyword, setNewExcludeKeyword] = useState('')
  const [parentSearch, setParentSearch] = useState('')
  const [showParentDropdown, setShowParentDropdown] = useState(false)
  
  // Amazon browse node search
  const [nodeSearch, setNodeSearch] = useState('')
  const [searchResults, setSearchResults] = useState<Array<{id: string, name: string, context_free_name?: string}>>([])
  const [isSearching, setIsSearching] = useState(false)
  const [showSearchResults, setShowSearchResults] = useState(false)

  useEffect(() => {
    if (open) {
      loadCategories()
    }
  }, [open])

  useEffect(() => {
    if (category) {
      setFormData({
        ...category,
        selection_rules: category.selection_rules || {},
        meta_title: category.meta_title || '',
        meta_description: category.meta_description || '',
        meta_keywords: category.meta_keywords || '',
        display_order: category.display_order || 0,
        parent_id: category.parent_id || null,
      })
      // Set parent search text if parent exists
      if (category.parent_id) {
        const parent = categories.find(c => c.id === category.parent_id)
        if (parent) {
          setParentSearch(parent.name)
        }
      } else {
        setParentSearch('')
      }
    } else {
      setFormData({
        name: '',
        slug: '',
        description: '',
        amazon_browse_node_ids: [],
        parent_id: null,
        is_active: true,
        meta_title: '',
        meta_description: '',
        meta_keywords: '',
        display_order: 0,
        selection_rules: {},
        max_products: 100,
        check_interval_hours: 6,
      })
      setParentSearch('')
    }
    setNewNodeId('')
    setNewIncludeKeyword('')
    setNewExcludeKeyword('')
  }, [category, open, categories])

  const loadCategories = async () => {
    try {
      const data = await categoriesAPI.list({ is_active: true })
      setCategories(data)
    } catch (error) {
      console.error('Kategoriler yüklenemedi:', error)
    }
  }

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/ğ/g, 'g')
      .replace(/ü/g, 'u')
      .replace(/ş/g, 's')
      .replace(/ı/g, 'i')
      .replace(/ö/g, 'o')
      .replace(/ç/g, 'c')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
  }

  const handleNameChange = (name: string) => {
    setFormData({
      ...formData,
      name,
      slug: generateSlug(name),
    })
  }

  const addNodeId = () => {
    if (newNodeId.trim() && !formData.amazon_browse_node_ids.includes(newNodeId.trim())) {
      setFormData({
        ...formData,
        amazon_browse_node_ids: [...formData.amazon_browse_node_ids, newNodeId.trim()]
      })
      setNewNodeId('')
    }
  }

  const removeNodeId = (nodeId: string) => {
    setFormData({
      ...formData,
      amazon_browse_node_ids: formData.amazon_browse_node_ids.filter(id => id !== nodeId)
    })
  }

  const searchAmazonNodes = async () => {
    if (!nodeSearch.trim() || isSearching) return
    
    setIsSearching(true)
    try {
      const response = await amazonAPI.searchBrowseNodes(nodeSearch)
      setSearchResults(response.nodes || [])
      setShowSearchResults(true)
      
      if (response.nodes.length === 0) {
        toast({
          title: 'Sonuç bulunamadı',
          description: 'Bu arama için kategori bulunamadı',
          variant: 'default',
        })
      }
    } catch (error: any) {
      toast({
        title: 'Arama hatası',
        description: error.response?.data?.detail || 'Amazon kategorileri aranamadı',
        variant: 'destructive',
      })
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  const addNodeFromSearch = (node: {id: string, name: string, context_free_name?: string}) => {
    if (!formData.amazon_browse_node_ids.includes(node.id)) {
      setFormData({
        ...formData,
        amazon_browse_node_ids: [...formData.amazon_browse_node_ids, node.id]
      })
      toast({
        title: 'Kategori eklendi',
        description: `${node.name} (${node.id})`,
        variant: 'success',
      })
    }
    setNodeSearch('')
    setSearchResults([])
    setShowSearchResults(false)
  }

  const addKeyword = (type: 'include' | 'exclude') => {
    const keyword = type === 'include' ? newIncludeKeyword : newExcludeKeyword
    if (!keyword.trim()) return

    const rules = formData.selection_rules || {}
    const existingKeywords = type === 'include' ? rules.include_keywords || [] : rules.exclude_keywords || []
    
    if (!existingKeywords.includes(keyword.trim())) {
      setFormData({
        ...formData,
        selection_rules: {
          ...rules,
          [type === 'include' ? 'include_keywords' : 'exclude_keywords']: [...existingKeywords, keyword.trim()]
        }
      })
    }
    
    if (type === 'include') setNewIncludeKeyword('')
    else setNewExcludeKeyword('')
  }

  const removeKeyword = (type: 'include' | 'exclude', keyword: string) => {
    const rules = formData.selection_rules || {}
    const key = type === 'include' ? 'include_keywords' : 'exclude_keywords'
    const keywords = rules[key] || []
    
    setFormData({
      ...formData,
      selection_rules: {
        ...rules,
        [key]: keywords.filter((k: string) => k !== keyword)
      }
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (category?.id) {
        await categoriesAPI.update(category.id, formData)
        toast({
          title: 'Başarılı',
          description: 'Kategori güncellendi',
          variant: 'success',
        })
      } else {
        await categoriesAPI.create(formData)
        toast({
          title: 'Başarılı',
          description: 'Kategori oluşturuldu',
          variant: 'success',
        })
      }
      onOpenChange(false)
      onSuccess?.()
    } catch (error: any) {
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'İşlem başarısız oldu',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {category ? 'Kategori Düzenle' : 'Yeni Kategori Ekle'}
            </DialogTitle>
            <DialogDescription>
              Kahve Makinesi gibi bir kategori oluşturun ve birden fazla Amazon node ekleyin
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="basic" className="mt-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="basic">Temel</TabsTrigger>
              <TabsTrigger value="nodes">Nodes</TabsTrigger>
              <TabsTrigger value="rules">Filtreler</TabsTrigger>
              <TabsTrigger value="seo">SEO</TabsTrigger>
            </TabsList>

            <TabsContent value="basic" className="mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Kategori Adı <span className="text-red-500">*</span></Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    placeholder="Kahve Makinesi"
                    required
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="slug">Slug <span className="text-red-500">*</span></Label>
                  <Input
                    id="slug"
                    value={formData.slug}
                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                    placeholder="kahve-makinesi"
                    required
                    className="font-mono text-sm"
                  />
                </div>

                <div className="col-span-2 grid gap-2">
                  <Label htmlFor="description">Açıklama</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Kategori hakkında kısa açıklama..."
                    rows={2}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="parent">Üst Kategori</Label>
                  <div className="relative">
                    <Input
                      id="parent"
                      value={parentSearch}
                      onChange={(e) => {
                        setParentSearch(e.target.value)
                        setShowParentDropdown(true)
                      }}
                      onFocus={() => setShowParentDropdown(true)}
                      onBlur={() => setTimeout(() => setShowParentDropdown(false), 200)}
                      placeholder="Ara veya seç..."
                      className="w-full"
                    />
                    {showParentDropdown && (
                      <div className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto">
                        <div
                          className="px-3 py-2 hover:bg-gray-100 cursor-pointer border-b"
                          onClick={() => {
                            setFormData({ ...formData, parent_id: null })
                            setParentSearch('')
                            setShowParentDropdown(false)
                          }}
                        >
                          <span className="text-gray-500 italic">Üst kategori yok</span>
                        </div>
                        {categories
                          .filter(c => c.id !== category?.id && c.name.toLowerCase().includes(parentSearch.toLowerCase()))
                          .map((cat) => (
                            <div
                              key={cat.id}
                              className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
                              onClick={() => {
                                setFormData({ ...formData, parent_id: cat.id })
                                setParentSearch(cat.name)
                                setShowParentDropdown(false)
                              }}
                            >
                              {cat.name}
                            </div>
                          ))}
                        {categories.filter(c => c.id !== category?.id && c.name.toLowerCase().includes(parentSearch.toLowerCase())).length === 0 && parentSearch && (
                          <div className="px-3 py-2 text-gray-500 text-sm">
                            Kategori bulunamadı
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <Label>Aktif</Label>
                    <p className="text-xs text-gray-500">Takip edilsin mi?</p>
                  </div>
                  <Switch
                    checked={formData.is_active}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="max_products">Maks. Ürün</Label>
                  <Input
                    id="max_products"
                    type="number"
                    value={formData.max_products}
                    onChange={(e) => setFormData({ ...formData, max_products: parseInt(e.target.value) })}
                    placeholder="100"
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="check_interval">Kontrol Aralığı (saat)</Label>
                  <Input
                    id="check_interval"
                    type="number"
                    value={formData.check_interval_hours}
                    onChange={(e) => setFormData({ ...formData, check_interval_hours: parseInt(e.target.value) })}
                    placeholder="6"
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="display_order_basic">Sıralama</Label>
                  <Input
                    id="display_order_basic"
                    type="number"
                    value={formData.display_order}
                    onChange={(e) => setFormData({ ...formData, display_order: parseInt(e.target.value) || 0 })}
                    placeholder="0"
                  />
                  <p className="text-xs text-gray-500">
                    Küçük sayılar önce gösterilir
                  </p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="nodes" className="space-y-4 mt-4">
              {/* Amazon Kategori Arama */}
              <div className="space-y-2 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <Label className="text-blue-900">🔍 Amazon Kategorisi Ara</Label>
                <p className="text-sm text-blue-700">
                  Ürün adı veya kategori yazarak Amazon'dan browse node ara
                </p>
                <div className="flex gap-2">
                  <Input
                    value={nodeSearch}
                    onChange={(e) => setNodeSearch(e.target.value)}
                    placeholder="Örn: kahve makinesi, robot süpürge..."
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), searchAmazonNodes())}
                    className="bg-white"
                  />
                  <Button 
                    type="button" 
                    onClick={searchAmazonNodes}
                    disabled={!nodeSearch.trim() || isSearching}
                  >
                    {isSearching ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Search className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                
                {/* Arama Sonuçları */}
                {showSearchResults && searchResults.length > 0 && (
                  <div className="mt-2 border rounded-md bg-white max-h-60 overflow-auto">
                    <div className="p-2 bg-gray-50 border-b text-xs font-medium text-gray-600">
                      {searchResults.length} kategori bulundu
                    </div>
                    {searchResults.map((node) => (
                      <div
                        key={node.id}
                        className="p-3 hover:bg-blue-50 cursor-pointer border-b last:border-b-0 transition-colors"
                        onClick={() => addNodeFromSearch(node)}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="font-medium text-sm">{node.name}</div>
                            {node.context_free_name && node.context_free_name !== node.name && (
                              <div className="text-xs text-gray-500 mt-0.5">{node.context_free_name}</div>
                            )}
                            <div className="text-xs text-gray-400 mt-1 font-mono">ID: {node.id}</div>
                          </div>
                          <Plus className="h-4 w-4 text-blue-600 flex-shrink-0 mt-1" />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Manuel Node ID Girişi */}
              <div className="space-y-2">
                <Label>Veya Manuel Node ID Ekle</Label>
                <p className="text-sm text-gray-500">
                  Node ID'yi biliyorsanız direkt ekleyebilirsiniz
                </p>
                <div className="flex gap-2">
                  <Input
                    value={newNodeId}
                    onChange={(e) => setNewNodeId(e.target.value)}
                    placeholder="13393813031"
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addNodeId())}
                  />
                  <Button type="button" onClick={addNodeId}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              {/* Eklenen Node'lar */}
              <div className="space-y-2">
                <Label>Ekli Browse Node'lar ({formData.amazon_browse_node_ids.length})</Label>

                <div className="flex flex-wrap gap-2">
                  {formData.amazon_browse_node_ids.map((nodeId) => (
                    <Badge key={nodeId} variant="secondary" className="pl-3 pr-1">
                      {nodeId}
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-auto p-1 ml-1"
                        onClick={() => removeNodeId(nodeId)}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </Badge>
                  ))}
                  {formData.amazon_browse_node_ids.length === 0 && (
                    <p className="text-sm text-gray-500">Henüz node eklenmedi. Yukarıdan arayarak veya manuel ekleyerek başlayın.</p>
                  )}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="rules" className="mt-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="grid gap-2">
                  <Label>Min. Rating</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="5"
                    value={formData.selection_rules?.min_rating || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      selection_rules: { ...formData.selection_rules, min_rating: parseFloat(e.target.value) || undefined }
                    })}
                    placeholder="4.0"
                  />
                </div>

                <div className="grid gap-2">
                  <Label>Min. Yorum Sayısı</Label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.selection_rules?.min_review_count || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      selection_rules: { ...formData.selection_rules, min_review_count: parseInt(e.target.value) || undefined }
                    })}
                    placeholder="50"
                  />
                </div>

                <div className="grid gap-2">
                  <Label>Min. İndirim (%)</Label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.selection_rules?.min_discount_percentage || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      selection_rules: { ...formData.selection_rules, min_discount_percentage: parseFloat(e.target.value) || undefined }
                    })}
                    placeholder="20"
                  />
                </div>

                <div className="grid gap-2">
                  <Label>Min. Fiyat (₺)</Label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.selection_rules?.min_price || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      selection_rules: { ...formData.selection_rules, min_price: parseFloat(e.target.value) || undefined }
                    })}
                    placeholder="100"
                  />
                </div>

                <div className="grid gap-2">
                  <Label>Maks. Fiyat (₺)</Label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.selection_rules?.max_price || ''}
                    onChange={(e) => setFormData({
                      ...formData,
                      selection_rules: { ...formData.selection_rules, max_price: parseFloat(e.target.value) || undefined }
                    })}
                    placeholder="5000"
                  />
                </div>

                <div className="flex items-center justify-between rounded-lg border p-3">
                  <Label className="text-sm">Prime</Label>
                  <Switch
                    checked={formData.selection_rules?.only_prime || false}
                    onCheckedChange={(checked) => setFormData({
                      ...formData,
                      selection_rules: { ...formData.selection_rules, only_prime: checked }
                    })}
                  />
                </div>

                <div className="col-span-3 grid gap-2">
                  <Label>İçermesi Gereken Kelimeler</Label>
                  <div className="flex gap-2">
                    <Input
                      value={newIncludeKeyword}
                      onChange={(e) => setNewIncludeKeyword(e.target.value)}
                      placeholder="premium, profesyonel"
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword('include'))}
                    />
                    <Button type="button" onClick={() => addKeyword('include')} size="sm">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {formData.selection_rules?.include_keywords && formData.selection_rules.include_keywords.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {formData.selection_rules.include_keywords.map((keyword) => (
                        <Badge key={keyword} variant="default">
                          {keyword}
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-auto p-1 ml-1"
                            onClick={() => removeKeyword('include', keyword)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>

                <div className="col-span-3 grid gap-2">
                  <Label>Hariç Tutulacak Kelimeler</Label>
                  <div className="flex gap-2">
                    <Input
                      value={newExcludeKeyword}
                      onChange={(e) => setNewExcludeKeyword(e.target.value)}
                      placeholder="ikinci el, yenilenmiş"
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword('exclude'))}
                    />
                    <Button type="button" onClick={() => addKeyword('exclude')} size="sm">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  {formData.selection_rules?.exclude_keywords && formData.selection_rules.exclude_keywords.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {formData.selection_rules.exclude_keywords.map((keyword) => (
                        <Badge key={keyword} variant="destructive">
                          {keyword}
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-auto p-1 ml-1"
                            onClick={() => removeKeyword('exclude', keyword)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="seo" className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 grid gap-2">
                  <Label htmlFor="meta_title">Meta Title</Label>
                  <Input
                    id="meta_title"
                    value={formData.meta_title}
                    onChange={(e) => setFormData({ ...formData, meta_title: e.target.value })}
                    placeholder="Kategori sayfası için özel başlık..."
                    maxLength={60}
                  />
                  <p className="text-xs text-gray-500">
                    {formData.meta_title?.length || 0}/60 karakter - Boş bırakılırsa kategori adı kullanılır
                  </p>
                </div>

                <div className="col-span-2 grid gap-2">
                  <Label htmlFor="meta_description">Meta Description</Label>
                  <Textarea
                    id="meta_description"
                    value={formData.meta_description}
                    onChange={(e) => setFormData({ ...formData, meta_description: e.target.value })}
                    placeholder="Arama motorları için açıklama..."
                    rows={3}
                    maxLength={160}
                  />
                  <p className="text-xs text-gray-500">
                    {formData.meta_description?.length || 0}/160 karakter - Google'da gösterilir
                  </p>
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="display_order">Görüntüleme Sırası</Label>
                  <Input
                    id="display_order"
                    type="number"
                    value={formData.display_order}
                    onChange={(e) => setFormData({ ...formData, display_order: parseInt(e.target.value) || 0 })}
                    placeholder="0"
                  />
                  <p className="text-xs text-gray-500">
                    Küçük sayılar önce gösterilir
                  </p>
                </div>
              </div>
            </TabsContent>
          </Tabs>

          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
              İptal
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Kaydediliyor...' : category ? 'Güncelle' : 'Oluştur'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
