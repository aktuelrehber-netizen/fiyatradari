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
import { crawlersAPI } from '@/utils/api-client'
import { 
  Plus, Trash2, Edit, Globe, Zap, TrendingUp, 
  CheckCircle2, XCircle, Activity, Settings, TestTube
} from 'lucide-react'

interface CrawlerConfig {
  id: number
  name: string
  description: string
  crawler_type: string
  use_proxy: boolean
  proxy_rotation: boolean
  concurrent_limit: number
  rate_limit_per_second: number
  delay_between_requests_min: number
  delay_between_requests_max: number
  timeout_seconds: number
  max_retries: number
  retry_delay_seconds: number
  user_agent: string | null
  custom_headers: any
  follow_redirects: boolean
  verify_ssl: boolean
  advanced_config: any
  is_active: boolean
  total_requests: number
  successful_requests: number
  failed_requests: number
  last_used_at: string | null
  created_at: string
  updated_at: string
}

export default function CrawlersManagementPage() {
  const { toast } = useToast()
  
  // State
  const [loading, setLoading] = useState(true)
  const [configs, setConfigs] = useState<CrawlerConfig[]>([])
  const [statistics, setStatistics] = useState<any>(null)
  const [selectedConfig, setSelectedConfig] = useState<CrawlerConfig | null>(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [filterType, setFilterType] = useState<string>('all')
  const [filterActive, setFilterActive] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    crawler_type: 'httpx',
    use_proxy: false,
    proxy_rotation: true,
    concurrent_limit: 5,
    rate_limit_per_second: 1.0,
    delay_between_requests_min: 1.0,
    delay_between_requests_max: 3.0,
    timeout_seconds: 30,
    max_retries: 3,
    retry_delay_seconds: 2.0,
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    follow_redirects: true,
    verify_ssl: true,
    is_active: true
  })

  // Load data
  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [filterType, filterActive])

  const loadData = async () => {
    try {
      const [configsData, statsData] = await Promise.all([
        crawlersAPI.listConfigs(
          filterType !== 'all' ? filterType : undefined,
          filterActive
        ),
        crawlersAPI.getStatistics()
      ])
      
      setConfigs(configsData)
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

  const handleToggleConfig = async (id: number, active: boolean) => {
    try {
      await crawlersAPI.toggleConfig(id, active)
      toast({
        title: "Başarılı",
        description: active ? "Crawler aktifleştirildi" : "Crawler devre dışı bırakıldı"
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

  const handleDeleteConfig = async (id: number, name: string) => {
    if (!confirm(`"${name}" crawler yapılandırmasını silmek istediğinize emin misiniz?`)) return
    
    try {
      await crawlersAPI.deleteConfig(id)
      toast({
        title: "Başarılı",
        description: "Crawler yapılandırması silindi"
      })
      loadData()
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "Crawler silinemedi",
        variant: "destructive"
      })
    }
  }

  const handleCreateConfig = async () => {
    try {
      await crawlersAPI.createConfig(formData)
      toast({
        title: "Başarılı",
        description: "Yeni crawler yapılandırması oluşturuldu"
      })
      setIsCreateDialogOpen(false)
      resetForm()
      loadData()
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "Crawler oluşturulamadı",
        variant: "destructive"
      })
    }
  }

  const handleEditConfig = async () => {
    if (!selectedConfig) return
    
    try {
      await crawlersAPI.updateConfig(selectedConfig.id, formData)
      toast({
        title: "Başarılı",
        description: "Crawler yapılandırması güncellendi"
      })
      setIsEditDialogOpen(false)
      setSelectedConfig(null)
      loadData()
    } catch (error: any) {
      toast({
        title: "Hata",
        description: error.response?.data?.detail || "Crawler güncellenemedi",
        variant: "destructive"
      })
    }
  }

  const openEditDialog = (config: CrawlerConfig) => {
    setSelectedConfig(config)
    setFormData({
      name: config.name,
      description: config.description,
      crawler_type: config.crawler_type,
      use_proxy: config.use_proxy,
      proxy_rotation: config.proxy_rotation,
      concurrent_limit: config.concurrent_limit,
      rate_limit_per_second: config.rate_limit_per_second,
      delay_between_requests_min: config.delay_between_requests_min,
      delay_between_requests_max: config.delay_between_requests_max,
      timeout_seconds: config.timeout_seconds,
      max_retries: config.max_retries,
      retry_delay_seconds: config.retry_delay_seconds,
      user_agent: config.user_agent || '',
      follow_redirects: config.follow_redirects,
      verify_ssl: config.verify_ssl,
      is_active: config.is_active
    })
    setIsEditDialogOpen(true)
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      crawler_type: 'httpx',
      use_proxy: false,
      proxy_rotation: true,
      concurrent_limit: 5,
      rate_limit_per_second: 1.0,
      delay_between_requests_min: 1.0,
      delay_between_requests_max: 3.0,
      timeout_seconds: 30,
      max_retries: 3,
      retry_delay_seconds: 2.0,
      user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      follow_redirects: true,
      verify_ssl: true,
      is_active: true
    })
  }

  const renderForm = () => (
    <div className="space-y-4 py-4">
      <div className="space-y-2">
        <Label>Yapılandırma Adı</Label>
        <Input
          value={formData.name}
          onChange={(e) => setFormData({...formData, name: e.target.value})}
          placeholder="Örn: Standart HTTPX Crawler"
        />
      </div>
      
      <div className="space-y-2">
        <Label>Açıklama</Label>
        <Textarea
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          placeholder="Crawler yapılandırması hakkında açıklama"
          rows={2}
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Crawler Tipi</Label>
          <Select
            value={formData.crawler_type}
            onValueChange={(value) => setFormData({...formData, crawler_type: value})}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="httpx">HTTPX (Hızlı)</SelectItem>
              <SelectItem value="playwright">Playwright (Tarayıcı)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div className="space-y-2">
          <Label>Eş Zamanlı Limit</Label>
          <Input
            type="number"
            min="1"
            max="100"
            value={formData.concurrent_limit}
            onChange={(e) => setFormData({...formData, concurrent_limit: parseInt(e.target.value)})}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center space-x-2">
          <Switch
            checked={formData.use_proxy}
            onCheckedChange={(checked) => setFormData({...formData, use_proxy: checked})}
          />
          <Label>Proxy Kullan</Label>
        </div>
        
        <div className="flex items-center space-x-2">
          <Switch
            checked={formData.proxy_rotation}
            onCheckedChange={(checked) => setFormData({...formData, proxy_rotation: checked})}
            disabled={!formData.use_proxy}
          />
          <Label>Proxy Rotasyonu</Label>
        </div>
      </div>
      
      <div className="space-y-2">
        <Label>Rate Limit (istek/saniye)</Label>
        <Input
          type="number"
          step="0.1"
          min="0.1"
          max="100"
          value={formData.rate_limit_per_second}
          onChange={(e) => setFormData({...formData, rate_limit_per_second: parseFloat(e.target.value)})}
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Min Gecikme (sn)</Label>
          <Input
            type="number"
            step="0.1"
            min="0"
            value={formData.delay_between_requests_min}
            onChange={(e) => setFormData({...formData, delay_between_requests_min: parseFloat(e.target.value)})}
          />
        </div>
        
        <div className="space-y-2">
          <Label>Max Gecikme (sn)</Label>
          <Input
            type="number"
            step="0.1"
            min="0"
            value={formData.delay_between_requests_max}
            onChange={(e) => setFormData({...formData, delay_between_requests_max: parseFloat(e.target.value)})}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2">
          <Label>Timeout (sn)</Label>
          <Input
            type="number"
            min="5"
            max="300"
            value={formData.timeout_seconds}
            onChange={(e) => setFormData({...formData, timeout_seconds: parseInt(e.target.value)})}
          />
        </div>
        
        <div className="space-y-2">
          <Label>Max Tekrar</Label>
          <Input
            type="number"
            min="0"
            max="10"
            value={formData.max_retries}
            onChange={(e) => setFormData({...formData, max_retries: parseInt(e.target.value)})}
          />
        </div>
        
        <div className="space-y-2">
          <Label>Tekrar Gecikme (sn)</Label>
          <Input
            type="number"
            step="0.1"
            min="0"
            value={formData.retry_delay_seconds}
            onChange={(e) => setFormData({...formData, retry_delay_seconds: parseFloat(e.target.value)})}
          />
        </div>
      </div>
      
      <div className="space-y-2">
        <Label>User Agent</Label>
        <Textarea
          value={formData.user_agent}
          onChange={(e) => setFormData({...formData, user_agent: e.target.value})}
          placeholder="Mozilla/5.0..."
          rows={2}
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center space-x-2">
          <Switch
            checked={formData.follow_redirects}
            onCheckedChange={(checked) => setFormData({...formData, follow_redirects: checked})}
          />
          <Label>Yönlendirmeleri Takip Et</Label>
        </div>
        
        <div className="flex items-center space-x-2">
          <Switch
            checked={formData.verify_ssl}
            onCheckedChange={(checked) => setFormData({...formData, verify_ssl: checked})}
          />
          <Label>SSL Doğrula</Label>
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
          <h1 className="text-3xl font-bold">Crawler Yönetimi</h1>
          <p className="text-muted-foreground mt-1">
            Web crawler yapılandırmalarını yönetin
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Yeni Crawler
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Yeni Crawler Yapılandırması</DialogTitle>
              <DialogDescription>
                Yeni bir web crawler profili oluşturun
              </DialogDescription>
            </DialogHeader>
            {renderForm()}
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                İptal
              </Button>
              <Button onClick={handleCreateConfig}>
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
              <CardTitle className="text-sm font-medium">Toplam Config</CardTitle>
              <Settings className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.total_configs}</div>
              <p className="text-xs text-muted-foreground">
                {statistics.active_configs} aktif
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Toplam İstek</CardTitle>
              <Activity className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statistics.total_requests.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                Tüm yapılandırmalar
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Başarılı</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {statistics.successful_requests.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                {statistics.overall_success_rate}% başarı oranı
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Başarısız</CardTitle>
              <XCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {statistics.failed_requests.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                Hatalı istek
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
                  <SelectItem value="httpx">HTTPX</SelectItem>
                  <SelectItem value="playwright">Playwright</SelectItem>
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

      {/* Configs List */}
      <div className="grid gap-4">
        {configs.map((config) => {
          const successRate = config.total_requests > 0 
            ? Math.round((config.successful_requests / config.total_requests) * 100)
            : 0
          
          return (
            <Card key={config.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <Globe className="w-5 h-5 text-muted-foreground" />
                      <CardTitle className="text-lg">{config.name}</CardTitle>
                      <Badge variant="outline">
                        {config.crawler_type}
                      </Badge>
                      {config.use_proxy && (
                        <Badge variant="outline" className="border-blue-500 text-blue-600">
                          Proxy
                        </Badge>
                      )}
                      {config.is_active ? (
                        <Badge variant="outline" className="border-green-500 text-green-600">
                          Aktif
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="border-gray-400 text-gray-600">
                          Kapalı
                        </Badge>
                      )}
                    </div>
                    <CardDescription>{config.description}</CardDescription>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={config.is_active}
                      onCheckedChange={(checked) => handleToggleConfig(config.id, checked)}
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openEditDialog(config)}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteConfig(config.id, config.name)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Eş Zamanlı Limit</p>
                    <p className="font-medium">{config.concurrent_limit}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Rate Limit</p>
                    <p className="font-medium">{config.rate_limit_per_second}/s</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Timeout</p>
                    <p className="font-medium">{config.timeout_seconds}s</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Max Tekrar</p>
                    <p className="font-medium">{config.max_retries}</p>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Toplam İstek</p>
                      <p className="font-medium text-lg">{config.total_requests.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Başarılı</p>
                      <p className="font-medium text-lg text-green-600">
                        {config.successful_requests.toLocaleString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Başarı Oranı</p>
                      <p className="font-medium text-lg">
                        <span className={successRate >= 80 ? 'text-green-600' : successRate >= 50 ? 'text-yellow-600' : 'text-red-600'}>
                          {successRate}%
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
                
                {config.last_used_at && (
                  <div className="mt-4 pt-4 border-t text-xs text-muted-foreground">
                    Son kullanım: {new Date(config.last_used_at).toLocaleString('tr-TR')}
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
        
        {configs.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Globe className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium">Henüz crawler yapılandırması yok</p>
              <p className="text-muted-foreground">
                Yeni bir crawler profili oluşturun
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Crawler Yapılandırmasını Düzenle</DialogTitle>
            <DialogDescription>
              Mevcut crawler profilini güncelleyin
            </DialogDescription>
          </DialogHeader>
          {renderForm()}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              İptal
            </Button>
            <Button onClick={handleEditConfig}>
              Güncelle
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
