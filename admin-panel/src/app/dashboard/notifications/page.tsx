"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, 
  DialogHeader, DialogTitle, DialogTrigger 
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/hooks/use-toast'
import { notificationsAPI } from '@/utils/api-client'
import { 
  Plus, Trash2, Edit, Send, Eye, Star, 
  MessageSquare, TrendingUp, CheckCircle2, Bell
} from 'lucide-react'

interface NotificationTemplate {
  id: number
  name: string
  description: string
  template_type: string
  message_template: string
  send_interval_minutes: number
  max_notifications_per_hour: number
  parse_mode: string
  disable_web_page_preview: boolean
  min_discount_percentage: number | null
  min_price: number | null
  max_price: number | null
  is_active: boolean
  is_default: boolean
  total_sent: number
  last_used_at: string | null
  created_at: string
  updated_at: string
}

export default function NotificationsManagementPage() {
  const { toast } = useToast()
  
  // State
  const [loading, setLoading] = useState(true)
  const [templates, setTemplates] = useState<NotificationTemplate[]>([])
  const [statistics, setStatistics] = useState<any>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<NotificationTemplate | null>(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isPreviewDialogOpen, setIsPreviewDialogOpen] = useState(false)
  const [previewData, setPreviewData] = useState<any>(null)
  const [filterType, setFilterType] = useState<string>('all')
  const [filterActive, setFilterActive] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    template_type: 'deal',
    message_template: '',
    send_interval_minutes: 5,
    max_notifications_per_hour: 12,
    parse_mode: 'Markdown',
    disable_web_page_preview: false,
    min_discount_percentage: null as number | null,
    min_price: null as number | null,
    max_price: null as number | null,
    is_active: true,
    is_default: false
  })

  // Default template examples
  const templateExamples = {
    deal: `🔥 *Yeni Fırsat!*

📦 {{product.title}}

💰 *Fiyat:* ~~{{deal.original_price}} TL~~ → *{{deal.deal_price}} TL*
🎯 *İndirim:* {{deal.discount_percentage}}% ({{deal.discount_amount}} TL)

⭐ Puan: {{product.rating}}/5 ({{product.review_count}} değerlendirme)

🛒 [Ürüne Git]({{product.detail_page_url}})

#fırsat #indirim`,
    price_drop: `📉 *Fiyat Düştü!*

{{product.title}}

Eski: {{old_price}} TL
Yeni: *{{new_price}} TL*

↓ {{price_drop_percentage}}% düşüş

[İncele]({{product.detail_page_url}})`,
    back_in_stock: `✅ *Stokta!*

{{product.title}}

Tekrar stokta!
💰 {{product.current_price}} TL

[Hemen Al]({{product.detail_page_url}})`
  }

  // Load data
  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [filterType, filterActive])

  const loadData = async () => {
    try {
      const [templatesData, statsData] = await Promise.all([
        notificationsAPI.listTemplates(
          filterType !== 'all' ? filterType : undefined,
          filterActive
        ),
        notificationsAPI.getStatistics()
      ])
      
      setTemplates(templatesData)
      setStatistics(statsData)
      setLoading(false)
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "Veri yüklenemedi",
        variant: "destructive"
      })
      setLoading(false)
    }
  }

  const handleToggleTemplate = async (id: number, active: boolean) => {
    try {
      await notificationsAPI.toggleTemplate(id, active)
      toast({
        title: "Başarılı",
        description: active ? "Şablon aktifleştirildi" : "Şablon devre dışı bırakıldı"
      })
      loadData()
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "İşlem başarısız",
        variant: "destructive"
      })
    }
  }

  const handleSetDefault = async (id: number, name: string) => {
    try {
      await notificationsAPI.setDefaultTemplate(id)
      toast({
        title: "Başarılı",
        description: `"${name}" varsayılan şablon olarak ayarlandı`
      })
      loadData()
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "İşlem başarısız",
        variant: "destructive"
      })
    }
  }

  const handleDeleteTemplate = async (id: number, name: string) => {
    if (!confirm(`"${name}" şablonunu silmek istediğinize emin misiniz?`)) return
    
    try {
      await notificationsAPI.deleteTemplate(id)
      toast({
        title: "Başarılı",
        description: "Şablon silindi"
      })
      loadData()
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "Şablon silinemedi",
        variant: "destructive"
      })
    }
  }

  const handleCreateTemplate = async () => {
    try {
      await notificationsAPI.createTemplate(formData)
      toast({
        title: "Başarılı",
        description: "Yeni bildirim şablonu oluşturuldu"
      })
      setIsCreateDialogOpen(false)
      resetForm()
      loadData()
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "Şablon oluşturulamadı",
        variant: "destructive"
      })
    }
  }

  const handleEditTemplate = async () => {
    if (!selectedTemplate) return
    
    try {
      await notificationsAPI.updateTemplate(selectedTemplate.id, formData)
      toast({
        title: "Başarılı",
        description: "Bildirim şablonu güncellendi"
      })
      setIsEditDialogOpen(false)
      setSelectedTemplate(null)
      loadData()
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "Şablon güncellenemedi",
        variant: "destructive"
      })
    }
  }

  const handlePreview = async (template: NotificationTemplate) => {
    try {
      const result = await notificationsAPI.previewTemplate(template.id)
      setPreviewData(result)
      setIsPreviewDialogOpen(true)
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "Önizleme oluşturulamadı",
        variant: "destructive"
      })
    }
  }

  const openEditDialog = (template: NotificationTemplate) => {
    setSelectedTemplate(template)
    setFormData({
      name: template.name,
      description: template.description,
      template_type: template.template_type,
      message_template: template.message_template,
      send_interval_minutes: template.send_interval_minutes,
      max_notifications_per_hour: template.max_notifications_per_hour,
      parse_mode: template.parse_mode,
      disable_web_page_preview: template.disable_web_page_preview,
      min_discount_percentage: template.min_discount_percentage,
      min_price: template.min_price,
      max_price: template.max_price,
      is_active: template.is_active,
      is_default: template.is_default
    })
    setIsEditDialogOpen(true)
  }

  const loadTemplateExample = (type: string) => {
    setFormData({
      ...formData,
      template_type: type,
      message_template: templateExamples[type as keyof typeof templateExamples] || ''
    })
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      template_type: 'deal',
      message_template: '',
      send_interval_minutes: 5,
      max_notifications_per_hour: 12,
      parse_mode: 'Markdown',
      disable_web_page_preview: false,
      min_discount_percentage: null,
      min_price: null,
      max_price: null,
      is_active: true,
      is_default: false
    })
  }

  const renderForm = () => (
    <div className="space-y-4 py-4">
      <div className="space-y-2">
        <Label>Şablon Adı</Label>
        <Input
          value={formData.name}
          onChange={(e) => setFormData({...formData, name: e.target.value})}
          placeholder="Örn: Standart Fırsat Bildirimi"
        />
      </div>
      
      <div className="space-y-2">
        <Label>Açıklama</Label>
        <Textarea
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          placeholder="Şablon hakkında açıklama"
          rows={2}
        />
      </div>
      
      <div className="space-y-2">
        <Label>Şablon Tipi</Label>
        <div className="flex gap-2">
          <Select
            value={formData.template_type}
            onValueChange={(value) => setFormData({...formData, template_type: value})}
          >
            <SelectTrigger className="flex-1">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="deal">Fırsat</SelectItem>
              <SelectItem value="price_drop">Fiyat Düşüşü</SelectItem>
              <SelectItem value="back_in_stock">Stokta</SelectItem>
              <SelectItem value="custom">Özel</SelectItem>
            </SelectContent>
          </Select>
          <Button
            type="button"
            variant="outline"
            onClick={() => loadTemplateExample(formData.template_type)}
          >
            Örnek Yükle
          </Button>
        </div>
      </div>
      
      <div className="space-y-2">
        <Label>Mesaj Şablonu (Jinja2)</Label>
        <Textarea
          value={formData.message_template}
          onChange={(e) => setFormData({...formData, message_template: e.target.value})}
          placeholder="Jinja2 template syntax kullanın: {{product.title}}"
          rows={12}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Değişkenler: product.title, product.rating, deal.discount_percentage, vb.
        </p>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Gönderim Aralığı (dakika)</Label>
          <Input
            type="number"
            min="1"
            max="1440"
            value={formData.send_interval_minutes}
            onChange={(e) => setFormData({...formData, send_interval_minutes: parseInt(e.target.value)})}
          />
        </div>
        
        <div className="space-y-2">
          <Label>Max Bildirim/Saat</Label>
          <Input
            type="number"
            min="1"
            max="100"
            value={formData.max_notifications_per_hour}
            onChange={(e) => setFormData({...formData, max_notifications_per_hour: parseInt(e.target.value)})}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Parse Mode</Label>
          <Select
            value={formData.parse_mode}
            onValueChange={(value) => setFormData({...formData, parse_mode: value})}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Markdown">Markdown</SelectItem>
              <SelectItem value="HTML">HTML</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div className="flex items-center space-x-2 pt-8">
          <Switch
            checked={formData.disable_web_page_preview}
            onCheckedChange={(checked) => setFormData({...formData, disable_web_page_preview: checked})}
          />
          <Label>Link Önizleme Devre Dışı</Label>
        </div>
      </div>
      
      <div className="border-t pt-4">
        <h4 className="text-sm font-medium mb-3">Filtreler (Opsiyonel)</h4>
        
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>Min İndirim (%)</Label>
            <Input
              type="number"
              min="0"
              max="100"
              value={formData.min_discount_percentage || ''}
              onChange={(e) => setFormData({
                ...formData, 
                min_discount_percentage: e.target.value ? parseFloat(e.target.value) : null
              })}
              placeholder="15"
            />
          </div>
          
          <div className="space-y-2">
            <Label>Min Fiyat (TL)</Label>
            <Input
              type="number"
              min="0"
              value={formData.min_price || ''}
              onChange={(e) => setFormData({
                ...formData, 
                min_price: e.target.value ? parseFloat(e.target.value) : null
              })}
              placeholder="0"
            />
          </div>
          
          <div className="space-y-2">
            <Label>Max Fiyat (TL)</Label>
            <Input
              type="number"
              min="0"
              value={formData.max_price || ''}
              onChange={(e) => setFormData({
                ...formData, 
                max_price: e.target.value ? parseFloat(e.target.value) : null
              })}
              placeholder="9999"
            />
          </div>
        </div>
      </div>
      
      <div className="flex items-center space-x-4 pt-2">
        <div className="flex items-center space-x-2">
          <Switch
            checked={formData.is_default}
            onCheckedChange={(checked) => setFormData({...formData, is_default: checked})}
          />
          <Label>Varsayılan Şablon</Label>
        </div>
      </div>
    </div>
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Yükleniyor...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Bildirim Şablonları</h1>
          <p className="text-muted-foreground mt-1">
            Telegram bildirim şablonlarını yönetin
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Yeni Şablon
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Yeni Bildirim Şablonu</DialogTitle>
              <DialogDescription>
                Telegram için özel bir mesaj şablonu oluşturun
              </DialogDescription>
            </DialogHeader>
            {renderForm()}
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                İptal
              </Button>
              <Button onClick={handleCreateTemplate}>
                Oluştur
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Toplam Şablon</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.total_templates}</div>
              <p className="text-xs text-muted-foreground">
                {statistics.active_templates} aktif
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Gönderilen Bildirim</CardTitle>
              <Send className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statistics.total_notifications_sent.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                Toplam gönderim
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">En Popüler</CardTitle>
              <TrendingUp className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-sm font-medium truncate">
                {statistics.most_used_template?.name || '-'}
              </div>
              <p className="text-xs text-muted-foreground">
                {statistics.most_used_template?.total_sent || 0} kullanım
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Şablon Tipleri</CardTitle>
              <Bell className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {Object.keys(statistics.template_types || {}).length}
              </div>
              <p className="text-xs text-muted-foreground">
                Farklı tip
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Label>Tip:</Label>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tümü</SelectItem>
                  <SelectItem value="deal">Fırsat</SelectItem>
                  <SelectItem value="price_drop">Fiyat Düşüşü</SelectItem>
                  <SelectItem value="back_in_stock">Stokta</SelectItem>
                  <SelectItem value="custom">Özel</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center gap-2">
              <Switch
                checked={filterActive}
                onCheckedChange={setFilterActive}
              />
              <Label>Sadece Aktif</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Templates List */}
      <div className="grid gap-4">
        {templates.map((template) => (
          <Card key={template.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-muted-foreground" />
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <Badge variant="outline">{template.template_type}</Badge>
                    {template.is_default && (
                      <Badge variant="outline" className="border-yellow-500 text-yellow-600">
                        <Star className="w-3 h-3 mr-1 fill-yellow-600" />
                        Varsayılan
                      </Badge>
                    )}
                    {template.is_active ? (
                      <Badge variant="outline" className="border-green-500 text-green-600">
                        Aktif
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="border-gray-400 text-gray-600">
                        Kapalı
                      </Badge>
                    )}
                  </div>
                  <CardDescription>{template.description}</CardDescription>
                </div>
                
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handlePreview(template)}
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                  {!template.is_default && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSetDefault(template.id, template.name)}
                    >
                      <Star className="w-4 h-4" />
                    </Button>
                  )}
                  <Switch
                    checked={template.is_active}
                    onCheckedChange={(checked) => handleToggleTemplate(template.id, checked)}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openEditDialog(template)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDeleteTemplate(template.id, template.name)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                <div>
                  <p className="text-muted-foreground">Gönderim Aralığı</p>
                  <p className="font-medium">{template.send_interval_minutes} dakika</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Max/Saat</p>
                  <p className="font-medium">{template.max_notifications_per_hour}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Parse Mode</p>
                  <p className="font-medium">{template.parse_mode}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Toplam Gönderim</p>
                  <p className="font-medium text-blue-600">{template.total_sent.toLocaleString()}</p>
                </div>
              </div>
              
              <div className="bg-muted rounded-lg p-3">
                <p className="text-xs font-medium text-muted-foreground mb-2">Şablon Önizleme:</p>
                <pre className="text-xs whitespace-pre-wrap font-mono">
                  {template.message_template.substring(0, 200)}
                  {template.message_template.length > 200 && '...'}
                </pre>
              </div>
              
              {template.min_discount_percentage && (
                <div className="mt-3 text-xs text-muted-foreground">
                  Min indirim: {template.min_discount_percentage}%
                </div>
              )}
            </CardContent>
          </Card>
        ))}
        
        {templates.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <MessageSquare className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium">Henüz şablon yok</p>
              <p className="text-muted-foreground">
                Yeni bir bildirim şablonu oluşturun
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Şablonu Düzenle</DialogTitle>
            <DialogDescription>
              Bildirim şablonunu güncelleyin
            </DialogDescription>
          </DialogHeader>
          {renderForm()}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              İptal
            </Button>
            <Button onClick={handleEditTemplate}>
              Güncelle
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog open={isPreviewDialogOpen} onOpenChange={setIsPreviewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Şablon Önizleme</DialogTitle>
            <DialogDescription>
              Örnek verilerle oluşturulmuş mesaj
            </DialogDescription>
          </DialogHeader>
          {previewData && (
            <div className="space-y-4">
              <div className="bg-muted rounded-lg p-4">
                <p className="text-sm whitespace-pre-wrap">
                  {previewData.rendered_message}
                </p>
              </div>
              <div className="text-xs text-muted-foreground">
                Parse Mode: {previewData.parse_mode}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setIsPreviewDialogOpen(false)}>
              Kapat
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
