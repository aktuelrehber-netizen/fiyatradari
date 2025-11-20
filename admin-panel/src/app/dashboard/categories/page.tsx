'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { categoriesAPI } from '@/utils/api-client'
import { Plus, Edit, Trash2, RefreshCw, ChevronRight, ChevronDown, Folder, FolderOpen } from 'lucide-react'
import { CategoryModal } from '@/components/modals/category-modal'
import { useToast } from '@/hooks/use-toast'

interface Category {
  id: number
  name: string
  slug: string
  description?: string
  amazon_browse_node_ids: string[]
  parent_id: number | null
  is_active: boolean
  product_count?: number
  active_deal_count?: number
  created_at?: string
  meta_title?: string
  meta_description?: string
  meta_keywords?: string
  display_order?: number
  selection_rules?: any
  max_products?: number
  check_interval_hours?: number
  children?: Category[]
}

export default function CategoriesPage() {
  const { toast } = useToast()
  const [categories, setCategories] = useState<Category[]>([])
  const [treeData, setTreeData] = useState<Category[]>([])
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null)

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    try {
      const data = await categoriesAPI.list()
      setCategories(data)
      // Build tree structure
      const tree = buildTree(data)
      setTreeData(tree)
    } catch (error) {
      // Silent fail - will show empty state
    } finally {
      setLoading(false)
    }
  }

  const buildTree = (items: Category[]): Category[] => {
    const map = new Map<number, Category>()
    const roots: Category[] = []

    // Create a map of all items
    items.forEach(item => {
      map.set(item.id, { ...item, children: [] })
    })

    // Build the tree
    items.forEach(item => {
      const node = map.get(item.id)!
      if (item.parent_id === null || item.parent_id === undefined) {
        roots.push(node)
      } else {
        const parent = map.get(item.parent_id)
        if (parent) {
          parent.children!.push(node)
        } else {
          // Parent not found, treat as root
          roots.push(node)
        }
      }
    })

    return roots
  }

  const toggleExpand = (id: number) => {
    setExpandedIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

  const expandAll = () => {
    const allIds = new Set<number>()
    const collectIds = (items: Category[]) => {
      items.forEach(item => {
        if (item.children && item.children.length > 0) {
          allIds.add(item.id)
          collectIds(item.children)
        }
      })
    }
    collectIds(treeData)
    setExpandedIds(allIds)
  }

  const collapseAll = () => {
    setExpandedIds(new Set())
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Bu kategoriyi silmek istediğinizden emin misiniz?')) {
      return
    }

    try {
      await categoriesAPI.delete(id)
      toast({
        title: 'Başarılı',
        description: 'Kategori silindi',
        variant: 'success',
      })
      loadCategories()
    } catch (error: any) {
      toast({
        title: 'Hata',
        description: error.response?.data?.detail || 'Silme işlemi başarısız oldu',
        variant: 'destructive',
      })
    }
  }

  const handleEdit = (category: Category) => {
    setSelectedCategory(category)
    setModalOpen(true)
  }

  const handleCreate = () => {
    setSelectedCategory(null)
    setModalOpen(true)
  }

  const handleModalClose = () => {
    setModalOpen(false)
    setSelectedCategory(null)
  }

  const renderTreeNode = (category: Category, level: number = 0): JSX.Element[] => {
    const isExpanded = expandedIds.has(category.id)
    const hasChildren = category.children && category.children.length > 0
    const elements: JSX.Element[] = []

    elements.push(
      <TableRow key={category.id} className="hover:bg-gray-50">
        <TableCell>
          <div className="flex items-center gap-2" style={{ paddingLeft: `${level * 24}px` }}>
            {hasChildren ? (
              <button
                onClick={() => toggleExpand(category.id)}
                className="p-0.5 hover:bg-gray-200 rounded"
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>
            ) : (
              <span className="w-5" />
            )}
            {hasChildren ? (
              isExpanded ? (
                <FolderOpen className="h-4 w-4 text-blue-500" />
              ) : (
                <Folder className="h-4 w-4 text-blue-500" />
              )
            ) : (
              <span className="w-4 h-4 rounded-full bg-gray-300" />
            )}
            <span className={hasChildren ? 'font-semibold' : 'font-medium'}>
              {category.name}
            </span>
          </div>
        </TableCell>
        <TableCell className="text-gray-600 font-mono text-xs">{category.slug}</TableCell>
        <TableCell className="text-gray-600 font-mono text-xs">
          {category.amazon_browse_node_ids?.length > 0 ? (
            <span className="bg-blue-50 px-2 py-0.5 rounded text-blue-700">
              {category.amazon_browse_node_ids.length} node
            </span>
          ) : (
            '-'
          )}
        </TableCell>
        <TableCell className="text-center">{category.product_count || 0}</TableCell>
        <TableCell className="text-center">{category.active_deal_count || 0}</TableCell>
        <TableCell className="text-center">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            category.is_active
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800'
          }`}>
            {category.is_active ? 'Aktif' : 'Pasif'}
          </span>
        </TableCell>
        <TableCell className="text-right">
          <div className="flex items-center justify-end gap-2">
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => handleEdit(category)}
            >
              <Edit className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => handleDelete(category.id)}
            >
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </div>
        </TableCell>
      </TableRow>
    )

    if (isExpanded && hasChildren) {
      category.children!.forEach(child => {
        elements.push(...renderTreeNode(child, level + 1))
      })
    }

    return elements
  }

  if (loading) {
    return <div className="text-center py-12">Yükleniyor...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Kategoriler</h1>
          <p className="text-gray-500 mt-1">
            Amazon kategorilerini ve ürün takip kurallarını yönetin
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={expandAll}>
            Tümünü Aç
          </Button>
          <Button variant="outline" size="sm" onClick={collapseAll}>
            Tümünü Kapat
          </Button>
          <Button variant="outline" size="sm" onClick={loadCategories}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Yenile
          </Button>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Yeni Kategori
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tüm Kategoriler ({categories.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Kategori Adı</TableHead>
                <TableHead>Slug</TableHead>
                <TableHead>Amazon Node ID</TableHead>
                <TableHead className="text-center">Ürün Sayısı</TableHead>
                <TableHead className="text-center">Aktif Fırsatlar</TableHead>
                <TableHead className="text-center">Durum</TableHead>
                <TableHead className="text-right">İşlemler</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {treeData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-gray-500 py-8">
                    Henüz kategori eklenmemiş
                  </TableCell>
                </TableRow>
              ) : (
                treeData.flatMap(category => renderTreeNode(category))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <CategoryModal
        open={modalOpen}
        onOpenChange={handleModalClose}
        category={selectedCategory as any}
        onSuccess={loadCategories}
      />
    </div>
  )
}
