'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { settingsAPI } from '@/utils/api-client'
import { Save, Eye, EyeOff, Check, Settings as SettingsIcon, Plus } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { TelegramTemplateEditor } from '@/components/telegram-template-editor'

interface Setting {
  key: string
  value: string
  data_type: string
  description: string
  group: string
  is_secret?: boolean
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([])
  const [formData, setFormData] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showSecrets, setShowSecrets] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  
  // New setting dialog state
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [newSetting, setNewSetting] = useState({
    key: '',
    value: '',
    description: '',
    group: 'proxy',
    data_type: 'string'
  })

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const data = await settingsAPI.list()
      // Sort by group first, then by key to maintain consistent order
      const sortedData = data.sort((a: Setting, b: Setting) => {
        if (a.group !== b.group) {
          return a.group.localeCompare(b.group)
        }
        return a.key.localeCompare(b.key)
      })
      setSettings(sortedData)
      // Initialize form data with current values
      const initialData: Record<string, string> = {}
      sortedData.forEach((setting: Setting) => {
        initialData[setting.key] = setting.value
      })
      setFormData(initialData)
    } catch (error) {
      // Silent fail - will show empty state
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (key: string, value: string) => {
    setFormData(prev => ({ ...prev, [key]: value }))
    setHasChanges(true)
    setSaveSuccess(false)
  }

  const handleSaveAll = async () => {
    setSaving(true)
    setSaveSuccess(false)
    try {
      // Only save changed values
      const changedSettings = settings.filter(
        setting => formData[setting.key] !== setting.value
      )
      
      if (changedSettings.length === 0) {
        alert('Değişiklik yapılmadı')
        setSaving(false)
        return
      }

      for (const setting of changedSettings) {
        await settingsAPI.update(setting.key, { value: formData[setting.key] })
      }
      
      // Update settings state without reloading (to maintain order)
      const updatedSettings = settings.map(setting => ({
        ...setting,
        value: formData[setting.key] || setting.value
      }))
      setSettings(updatedSettings)
      
      setHasChanges(false)
      setSaveSuccess(true)
      
      // Hide success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Kaydetme başarısız oldu')
    } finally {
      setSaving(false)
    }
  }

  const handleCreateSetting = async () => {
    if (!newSetting.key || !newSetting.description) {
      alert('Key ve Description alanları zorunludur')
      return
    }

    try {
      const createdSetting = await settingsAPI.create(newSetting)
      
      // Add new setting to state (sorted position)
      const newSettings = [...settings, createdSetting].sort((a, b) => {
        if (a.group !== b.group) {
          return a.group.localeCompare(b.group)
        }
        return a.key.localeCompare(b.key)
      })
      setSettings(newSettings)
      
      // Add to formData
      setFormData(prev => ({
        ...prev,
        [createdSetting.key]: createdSetting.value
      }))
      
      setIsDialogOpen(false)
      setNewSetting({
        key: '',
        value: '',
        description: '',
        group: 'proxy',
        data_type: 'string'
      })
      alert('Yeni ayar eklendi!')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Ayar eklenemedi')
    }
  }

  const groupSettings = (group: string) => {
    return settings.filter(s => s.group === group)
  }

  const isSecretField = (key: string) => {
    return key.includes('secret') || key.includes('password') || key.includes('token')
  }

  const renderSettingField = (setting: Setting) => (
    <div key={setting.key} className="space-y-2">
      <Label htmlFor={setting.key}>{setting.description || setting.key}</Label>
      <Input
        id={setting.key}
        type={isSecretField(setting.key) && !showSecrets ? 'password' : 'text'}
        value={formData[setting.key] || ''}
        onChange={(e) => handleInputChange(setting.key, e.target.value)}
        placeholder={setting.description}
      />
      {setting.key === 'proxy_enabled' && (
        <p className="text-xs text-muted-foreground">
          Proxy kullanımı: true veya false
        </p>
      )}
      {setting.key === 'http_proxy' && (
        <p className="text-xs text-muted-foreground">
          Format: http://user:pass@proxy.com:8080
        </p>
      )}
      {setting.key === 'proxy_list' && (
        <p className="text-xs text-muted-foreground">
          Virgülle ayrılmış liste: proxy1.com:8080,proxy2.com:8080
        </p>
      )}
    </div>
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <SettingsIcon className="h-12 w-12 animate-spin mx-auto text-gray-400" />
          <p className="mt-4 text-muted-foreground">Ayarlar yükleniyor...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Ayarlar</h1>
          <p className="text-muted-foreground mt-2">
            Sistem ayarlarını ve entegrasyonları yönetin
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSecrets(!showSecrets)}
          >
            {showSecrets ? (
              <><EyeOff className="h-4 w-4 mr-2" /> Gizli Alanları Gizle</>
            ) : (
              <><Eye className="h-4 w-4 mr-2" /> Gizli Alanları Göster</>
            )}
          </Button>
          <Button
            onClick={handleSaveAll}
            disabled={saving || !hasChanges}
            className="min-w-[140px]"
          >
            {saving ? (
              <><SettingsIcon className="h-4 w-4 mr-2 animate-spin" /> Kaydediliyor...</>
            ) : saveSuccess ? (
              <><Check className="h-4 w-4 mr-2" /> Kaydedildi!</>
            ) : (
              <><Save className="h-4 w-4 mr-2" /> Tümünü Kaydet</>
            )}
          </Button>
        </div>
      </div>

      {/* Success Banner */}
      {saveSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Check className="h-5 w-5 text-green-600" />
            <p className="text-sm text-green-900 font-medium">
              Ayarlar başarıyla kaydedildi!
            </p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="amazon" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="amazon">Amazon API</TabsTrigger>
          <TabsTrigger value="telegram">Telegram</TabsTrigger>
          <TabsTrigger value="openai">OpenAI API</TabsTrigger>
          <TabsTrigger value="proxy">Proxy</TabsTrigger>
        </TabsList>

        {/* Amazon Tab */}
        <TabsContent value="amazon" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Amazon Product Advertising API</CardTitle>
              <CardDescription>
                Amazon PA API 5.0 bağlantı ayarları. Ürün verilerini çekmek için gereklidir.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {groupSettings('amazon').length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>Amazon API ayarları bulunamadı</p>
                </div>
              ) : (
                groupSettings('amazon').map(renderSettingField)
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Telegram Tab */}
        <TabsContent value="telegram" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Telegram Bot</CardTitle>
              <CardDescription>
                Telegram bot token ve kanal ayarları. Fırsat bildirimlerini göndermek için kullanılır.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {groupSettings('telegram').filter(s => !s.key.includes('template')).length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>Telegram ayarları bulunamadı</p>
                </div>
              ) : (
                groupSettings('telegram')
                  .filter(s => !s.key.includes('template'))
                  .map(renderSettingField)
              )}
            </CardContent>
          </Card>

          {/* Telegram Template Editor */}
          <TelegramTemplateEditor onSave={() => {
            loadSettings()
          }} />
        </TabsContent>

        {/* OpenAI Tab */}
        <TabsContent value="openai" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>OpenAI API</CardTitle>
              <CardDescription>
                OpenAI API bağlantı ayarları. GPT modelleri ile ürün açıklamaları ve içerik üretimi için kullanılır.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {groupSettings('openai').length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <p>OpenAI API ayarları bulunamadı</p>
                  <p className="text-sm mt-2">API Key eklemek için aşağıdaki ayarları tanımlayın:</p>
                  <ul className="text-xs mt-4 space-y-1">
                    <li><strong>openai_api_key</strong> - OpenAI API Key</li>
                    <li><strong>openai_model</strong> - Kullanılacak model (örn: gpt-4, gpt-3.5-turbo)</li>
                    <li><strong>openai_max_tokens</strong> - Maksimum token sayısı</li>
                  </ul>
                </div>
              ) : (
                <>
                  <div className="bg-purple-50 dark:bg-purple-950 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                    <p className="text-sm text-purple-900 dark:text-purple-100">
                      <strong>🤖 OpenAI Kullanım Alanları</strong>
                    </p>
                    <ul className="text-xs text-purple-700 dark:text-purple-300 mt-2 space-y-1 ml-4 list-disc">
                      <li><strong>Ürün Açıklamaları:</strong> Otomatik ürün açıklaması oluşturma</li>
                      <li><strong>SEO İçeriği:</strong> Meta açıklamaları ve başlıklar</li>
                      <li><strong>Kategori Açıklamaları:</strong> Dinamik kategori içeriği</li>
                      <li><strong>Fırsat Özetleri:</strong> Deal özetleri ve highlight'lar</li>
                    </ul>
                  </div>
                  
                  <div className="space-y-4">
                    {groupSettings('openai').map(renderSettingField)}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Proxy Tab */}
        <TabsContent value="proxy" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>🌐 Proxy Ayarları</CardTitle>
                  <CardDescription>
                    Web crawler için proxy ayarları. Bot detection bypass için kullanılır.
                  </CardDescription>
                </div>
                <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm">
                      <Plus className="h-4 w-4 mr-2" />
                      Yeni Ayar Ekle
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                      <DialogTitle>Yeni Proxy Ayarı Ekle</DialogTitle>
                      <DialogDescription>
                        Yeni bir proxy ayarı tanımlayın. Key benzersiz olmalıdır.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label htmlFor="new-key">Key *</Label>
                        <Input
                          id="new-key"
                          placeholder="proxy_host"
                          value={newSetting.key}
                          onChange={(e) => setNewSetting({...newSetting, key: e.target.value})}
                        />
                        <p className="text-xs text-muted-foreground">
                          Örnek: proxy_host, proxy_port, proxy_username
                        </p>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="new-description">Açıklama *</Label>
                        <Input
                          id="new-description"
                          placeholder="Proxy sunucusu host adresi"
                          value={newSetting.description}
                          onChange={(e) => setNewSetting({...newSetting, description: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="new-value">Değer</Label>
                        <Input
                          id="new-value"
                          placeholder="proxy.example.com"
                          value={newSetting.value}
                          onChange={(e) => setNewSetting({...newSetting, value: e.target.value})}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="new-group">Grup</Label>
                        <Select
                          value={newSetting.group}
                          onValueChange={(value) => setNewSetting({...newSetting, group: value})}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="proxy">Proxy</SelectItem>
                            <SelectItem value="amazon">Amazon</SelectItem>
                            <SelectItem value="telegram">Telegram</SelectItem>
                            <SelectItem value="openai">OpenAI</SelectItem>
                            <SelectItem value="general">Genel</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                        İptal
                      </Button>
                      <Button onClick={handleCreateSetting}>
                        Ekle
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {groupSettings('proxy').length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-muted-foreground mb-4">
                    Proxy ayarları henüz eklenmemiş
                  </p>
                  <Button variant="outline" onClick={() => setIsDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    İlk Ayarı Ekle
                  </Button>
                </div>
              ) : (
                <>
                  <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <p className="text-sm text-blue-900 dark:text-blue-100">
                      <strong>💡 Proxy Kullanım Rehberi</strong>
                    </p>
                    <ul className="text-xs text-blue-700 dark:text-blue-300 mt-2 space-y-1 ml-4 list-disc">
                      <li><strong>Tek Proxy:</strong> http_proxy field'ını kullan</li>
                      <li><strong>Proxy Listesi:</strong> proxy_list ile rotation</li>
                      <li><strong>Premium Proxy:</strong> host, port, user, pass ile authentication</li>
                    </ul>
                  </div>
                  
                  <div className="space-y-4">
                    {groupSettings('proxy').map(renderSettingField)}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
